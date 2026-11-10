from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_admin
from app.models.assessment import AssessmentSession, AssessmentConfig
from app.models.result import AssessmentResult
from app.models.technology import Technology
from app.models.user import User
from app.schemas.result import ResultOut, ShortlistRequest, ShortlistResponse
from app.services.evaluation_service import evaluate_session

router = APIRouter(prefix="/api/admin/results", tags=["Admin - Results"])


def _enrich_result(result: AssessmentResult, session: AssessmentSession, config: AssessmentConfig, tech: Technology) -> ResultOut:
    out = ResultOut.model_validate(result)
    out.candidate_name = session.candidate_name
    out.candidate_email = session.candidate_email
    out.assessment_title = config.title if config else None
    out.technology_name = tech.name if tech else None
    return out


@router.get("", response_model=list[ResultOut])
async def list_results(
    config_id: Optional[str] = Query(None),
    passed: Optional[bool] = Query(None),
    shortlisted: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """List all results, optionally filtered."""
    # Get configs owned by this recruiter
    config_result = await db.execute(
        select(AssessmentConfig).where(AssessmentConfig.created_by == current_user.id)
    )
    recruiter_configs = {c.id: c for c in config_result.scalars().all()}

    filters = [AssessmentSession.config_id.in_(recruiter_configs.keys())]
    if config_id:
        filters.append(AssessmentSession.config_id == config_id)

    sessions_result = await db.execute(
        select(AssessmentSession).where(and_(*filters))
    )
    sessions = {s.id: s for s in sessions_result.scalars().all()}

    result_filters = [AssessmentResult.session_id.in_(sessions.keys())]
    if passed is not None:
        result_filters.append(AssessmentResult.passed == passed)
    if shortlisted is not None:
        result_filters.append(AssessmentResult.shortlisted == shortlisted)

    results_q = await db.execute(
        select(AssessmentResult)
        .where(and_(*result_filters))
        .order_by(AssessmentResult.evaluated_at.desc())
    )
    results = results_q.scalars().all()

    # Load technologies
    tech_map = {}
    for config in recruiter_configs.values():
        if config.technology_id not in tech_map:
            t = await db.execute(select(Technology).where(Technology.id == config.technology_id))
            tech = t.scalar_one_or_none()
            if tech:
                tech_map[config.technology_id] = tech

    output = []
    for r in results:
        session = sessions.get(r.session_id)
        if not session:
            continue
        config = recruiter_configs.get(session.config_id)
        tech = tech_map.get(config.technology_id) if config else None
        out = _enrich_result(r, session, config, tech)
        output.append(out)
    return output


@router.get("/{session_id}", response_model=ResultOut)
async def get_result(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    result = await db.execute(
        select(AssessmentResult).where(AssessmentResult.session_id == session_id)
    )
    assessment_result = result.scalar_one_or_none()
    if not assessment_result:
        raise HTTPException(status_code=404, detail="Result not found")

    session_r = await db.execute(select(AssessmentSession).where(AssessmentSession.id == session_id))
    session = session_r.scalar_one_or_none()
    config_r = await db.execute(select(AssessmentConfig).where(AssessmentConfig.id == session.config_id))
    config = config_r.scalar_one_or_none()
    tech_r = await db.execute(select(Technology).where(Technology.id == config.technology_id))
    tech = tech_r.scalar_one_or_none()

    return _enrich_result(assessment_result, session, config, tech)


@router.post("/shortlist", response_model=ShortlistResponse)
async def shortlist_candidates(
    data: ShortlistRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Apply shortlisting criteria and mark candidates."""
    sessions_r = await db.execute(
        select(AssessmentSession).where(AssessmentSession.config_id == data.config_id)
    )
    sessions = {s.id: s for s in sessions_r.scalars().all()}

    results_r = await db.execute(
        select(AssessmentResult).where(AssessmentResult.session_id.in_(sessions.keys()))
    )
    all_results = results_r.scalars().all()

    shortlisted_out = []
    rejected_out = []

    for r in all_results:
        meets_min = r.percentage >= data.min_percentage
        meets_max = data.max_percentage is None or r.percentage <= data.max_percentage
        should_shortlist = meets_min and meets_max

        r.shortlisted = should_shortlist
        r.shortlisted_at = datetime.utcnow()
        r.shortlisted_by = current_user.id

        session = sessions.get(r.session_id)
        out = ResultOut.model_validate(r)
        out.candidate_name = session.candidate_name if session else None
        out.candidate_email = session.candidate_email if session else None
        if should_shortlist:
            shortlisted_out.append(out)
        else:
            rejected_out.append(out)

    await db.flush()
    await db.commit()

    return ShortlistResponse(
        shortlisted=shortlisted_out,
        rejected=rejected_out,
        total_candidates=len(all_results),
        shortlisted_count=len(shortlisted_out),
        min_percentage=data.min_percentage,
    )


@router.post("/{session_id}/re-evaluate", response_model=ResultOut)
async def re_evaluate(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """Re-trigger AI evaluation for a session."""
    session_r = await db.execute(select(AssessmentSession).where(AssessmentSession.id == session_id))
    session = session_r.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status not in ("submitted", "evaluated"):
        raise HTTPException(status_code=400, detail="Session not yet submitted")

    result = await evaluate_session(db, session)
    return ResultOut.model_validate(result)


@router.get("/analytics/summary")
async def analytics_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """Get dashboard analytics for the recruiter."""
    from sqlalchemy import func

    config_r = await db.execute(
        select(AssessmentConfig).where(AssessmentConfig.created_by == current_user.id)
    )
    configs = config_r.scalars().all()
    config_ids = [c.id for c in configs]

    session_r = await db.execute(
        select(AssessmentSession).where(AssessmentSession.config_id.in_(config_ids))
    )
    sessions = session_r.scalars().all()
    session_ids = [s.id for s in sessions]

    result_r = await db.execute(
        select(AssessmentResult).where(AssessmentResult.session_id.in_(session_ids))
    )
    results = result_r.scalars().all()

    total = len(results)
    passed = sum(1 for r in results if r.passed)
    shortlisted = sum(1 for r in results if r.shortlisted)
    avg_score = sum(r.percentage for r in results) / max(total, 1)

    return {
        "total_assessments": len(configs),
        "total_candidates": total,
        "total_passed": passed,
        "total_shortlisted": shortlisted,
        "pass_rate": round(passed / max(total, 1) * 100, 1),
        "avg_score": round(avg_score, 1),
    }
