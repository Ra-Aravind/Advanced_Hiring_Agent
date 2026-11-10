from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_admin
from app.models.assessment import AssessmentConfig, AssessmentSession
from app.models.technology import Technology
from app.models.user import User
from app.schemas.assessment import (
    AssessmentConfigCreate, AssessmentConfigUpdate, AssessmentConfigOut,
    GenerateSessionRequest, SessionOut, AgentCommandRequest, AgentCommandResponse,
)
from app.services import assessment_service
from app.services.ai_service import parse_recruiter_command

router = APIRouter(prefix="/api/admin/assessments", tags=["Admin - Assessments"])


@router.post("/agent/parse", response_model=AgentCommandResponse)
async def parse_command(
    data: AgentCommandRequest,
    _: User = Depends(get_current_admin),
):
    """Parse a natural language recruiter command into an assessment config draft."""
    result = await parse_recruiter_command(data.command)
    return AgentCommandResponse(
        success=result["success"],
        parsed_config=result.get("config"),
        message="Command parsed successfully" if result["success"] else "Parsing failed",
        raw_response=result.get("raw_response"),
    )


@router.get("", response_model=list[AssessmentConfigOut])
async def list_assessments(
    is_active: Optional[bool] = Query(None),
    technology_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    filters = [AssessmentConfig.created_by == current_user.id]
    if is_active is not None:
        filters.append(AssessmentConfig.is_active == is_active)
    if technology_id:
        filters.append(AssessmentConfig.technology_id == technology_id)

    result = await db.execute(
        select(AssessmentConfig)
        .where(*filters)
        .order_by(AssessmentConfig.created_at.desc())
    )
    configs = result.scalars().all()

    # Enrich with technology info and session counts
    output = []
    for config in configs:
        tech_result = await db.execute(select(Technology).where(Technology.id == config.technology_id))
        tech = tech_result.scalar_one_or_none()

        count_result = await db.execute(
            select(func.count(AssessmentSession.id))
            .where(AssessmentSession.config_id == config.id)
        )
        session_count = count_result.scalar()

        out = AssessmentConfigOut.model_validate(config)
        out.technology_name = tech.name if tech else "Unknown"
        out.technology_icon = tech.icon if tech else "📋"
        out.session_count = session_count
        output.append(out)
    return output


@router.post("", response_model=AssessmentConfigOut, status_code=201)
async def create_assessment(
    data: AssessmentConfigCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    # Validate difficulty mix sums to total_questions
    mix = data.difficulty_mix
    mix_total = mix.beginner + mix.intermediate + mix.advanced
    if mix_total != data.total_questions:
        raise HTTPException(
            status_code=422,
            detail=f"Difficulty mix ({mix_total}) must equal total_questions ({data.total_questions})",
        )

    config = await assessment_service.create_assessment_config(db, data, current_user.id)
    tech_result = await db.execute(select(Technology).where(Technology.id == config.technology_id))
    tech = tech_result.scalar_one_or_none()

    out = AssessmentConfigOut.model_validate(config)
    out.technology_name = tech.name if tech else "Unknown"
    out.technology_icon = tech.icon if tech else "📋"
    return out


@router.get("/{config_id}", response_model=AssessmentConfigOut)
async def get_assessment(
    config_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    result = await db.execute(select(AssessmentConfig).where(AssessmentConfig.id == config_id))
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="Assessment not found")

    tech_result = await db.execute(select(Technology).where(Technology.id == config.technology_id))
    tech = tech_result.scalar_one_or_none()

    count_result = await db.execute(
        select(func.count(AssessmentSession.id)).where(AssessmentSession.config_id == config_id)
    )

    out = AssessmentConfigOut.model_validate(config)
    out.technology_name = tech.name if tech else "Unknown"
    out.technology_icon = tech.icon if tech else "📋"
    out.session_count = count_result.scalar()
    return out


@router.put("/{config_id}", response_model=AssessmentConfigOut)
async def update_assessment(
    config_id: str,
    data: AssessmentConfigUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    result = await db.execute(select(AssessmentConfig).where(AssessmentConfig.id == config_id))
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="Assessment not found")

    tech_result = await db.execute(select(Technology).where(Technology.id == config.technology_id))
    tech = tech_result.scalar_one_or_none()
    technology_name = tech.name if tech else "Unknown"
    technology_icon = tech.icon if tech else "📋"

    update_data = data.model_dump(exclude_unset=True)
    if "difficulty_mix" in update_data and update_data["difficulty_mix"]:
        update_data["difficulty_mix"] = update_data["difficulty_mix"].model_dump() if hasattr(update_data["difficulty_mix"], "model_dump") else update_data["difficulty_mix"]
    for key, value in update_data.items():
        setattr(config, key, value)
    await db.flush()
    await db.commit()
    await db.refresh(config)

    out = AssessmentConfigOut.model_validate(config)
    out.technology_name = technology_name
    out.technology_icon = technology_icon
    return out


@router.delete("/{config_id}", status_code=204)
async def delete_assessment(
    config_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """Permanently delete an assessment and all its sessions/results."""
    from app.models.assessment import AssessmentSession, CandidateAnswer
    from app.models.result import AssessmentResult

    result = await db.execute(select(AssessmentConfig).where(AssessmentConfig.id == config_id))
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="Assessment not found")

    # Get all session IDs for this config
    sessions_result = await db.execute(select(AssessmentSession.id).where(AssessmentSession.config_id == config_id))
    session_ids = [row[0] for row in sessions_result.fetchall()]

    if session_ids:
        # Delete AssessmentResults and CandidateAnswers manually
        await db.execute(AssessmentResult.__table__.delete().where(AssessmentResult.session_id.in_(session_ids)))
        await db.execute(CandidateAnswer.__table__.delete().where(CandidateAnswer.session_id.in_(session_ids)))
        # Delete AssessmentSessions
        await db.execute(AssessmentSession.__table__.delete().where(AssessmentSession.config_id == config_id))

    await db.delete(config)
    await db.commit()
    return None


@router.get("/{config_id}/sessions", response_model=list[SessionOut])
async def list_sessions(
    config_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """Return all candidate sessions for an assessment, enriched with result scores."""
    from app.models.result import AssessmentResult

    result = await db.execute(
        select(AssessmentSession)
        .where(AssessmentSession.config_id == config_id)
        .order_by(AssessmentSession.created_at.desc())
    )
    sessions = result.scalars().all()

    # Get config + technology for enrichment
    config_result = await db.execute(select(AssessmentConfig).where(AssessmentConfig.id == config_id))
    config = config_result.scalar_one_or_none()
    tech = None
    if config:
        tech_result = await db.execute(select(Technology).where(Technology.id == config.technology_id))
        tech = tech_result.scalar_one_or_none()

    # Bulk-fetch all results for these sessions in one query
    session_ids = [s.id for s in sessions]
    results_map: dict = {}
    if session_ids:
        res_rows = await db.execute(
            select(AssessmentResult).where(AssessmentResult.session_id.in_(session_ids))
        )
        for r in res_rows.scalars().all():
            results_map[r.session_id] = r

    output = []
    for s in sessions:
        out = SessionOut.model_validate(s)
        if config:
            out.assessment_title = config.title
            out.duration_minutes = config.duration_minutes
            out.total_questions = config.total_questions
        if tech:
            out.technology_name = tech.name

        res_obj = results_map.get(s.id)
        if res_obj:
            out.score = res_obj.total_score
            out.percentage = res_obj.percentage

        output.append(out)
    return output
