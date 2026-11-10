from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import asyncio

from app.core.database import get_db, AsyncSessionLocal
from app.models.assessment import AssessmentSession, AssessmentConfig
from app.models.result import AssessmentResult
from app.models.technology import Technology
from app.schemas.assessment import SessionStart, AnswerSubmit, SessionWithQuestions, SessionOut
from app.schemas.result import ResultOut
from app.services import assessment_service
from app.services.evaluation_service import evaluate_session

router = APIRouter(prefix="/api/candidate", tags=["Candidate"])


@router.get("/config/{access_code}")
async def get_assessment_info(
    access_code: str,
    db: AsyncSession = Depends(get_db),
):
    """Validate access code and return assessment info (before starting)."""
    config = await assessment_service.get_config_by_code(db, access_code)
    
    tech_result = await db.execute(select(Technology).where(Technology.id == config.technology_id))
    tech = tech_result.scalar_one_or_none()

    return {
        "access_code": config.access_code,
        "assessment_title": config.title,
        "technology": tech.name if tech else "Unknown",
        "technology_icon": tech.icon if tech else "📋",
        "total_questions": config.total_questions,
        "duration_minutes": config.duration_minutes,
        "passing_score": config.passing_score,
        "instructions": config.instructions,
    }


@router.post("/config/{access_code}/start", response_model=SessionWithQuestions)
async def start_assessment(
    access_code: str,
    data: SessionStart,
    db: AsyncSession = Depends(get_db),
):
    """Start the assessment - returns new session id and questions."""
    config = await assessment_service.get_config_by_code(db, access_code)
    
    session = await assessment_service.start_new_session(db, config, data)
    questions = await assessment_service.get_sanitized_questions(db, session.question_ids)

    tech_result = await db.execute(select(Technology).where(Technology.id == config.technology_id))
    tech = tech_result.scalar_one_or_none()

    session_out = SessionOut.model_validate(session)
    session_out.assessment_title = config.title
    session_out.technology_name = tech.name if tech else ""
    session_out.duration_minutes = config.duration_minutes
    session_out.total_questions = config.total_questions

    return SessionWithQuestions(session=session_out, questions=questions)


@router.get("/session/{session_id}", response_model=SessionWithQuestions)
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get active session details and questions for the test page."""
    session = await assessment_service.get_session_by_id(db, session_id)
    questions = await assessment_service.get_sanitized_questions(db, session.question_ids)
    
    config = session.config
    tech_r = await db.execute(select(Technology).where(Technology.id == config.technology_id))
    tech = tech_r.scalar_one_or_none()

    session_out = SessionOut.model_validate(session)
    session_out.assessment_title = config.title
    session_out.technology_name = tech.name if tech else ""
    session_out.duration_minutes = config.duration_minutes
    session_out.total_questions = config.total_questions

    return SessionWithQuestions(session=session_out, questions=questions)


@router.post("/session/{session_id}/answer")
async def save_answer(
    session_id: str,
    data: AnswerSubmit,
    db: AsyncSession = Depends(get_db),
):
    """Save/update a single answer during the assessment."""
    session = await assessment_service.get_session_by_id(db, session_id)
    await assessment_service.save_answer(
        db,
        session,
        data.question_id,
        data.answer_text,
        data.selected_option,
        data.time_spent_seconds,
    )
    return {"message": "Answer saved"}


async def _background_evaluate(session_id: str):
    """Run evaluation in a new DB session."""
    async with AsyncSessionLocal() as db:
        try:
            await evaluate_session(db, session_id)
        except Exception as e:
            import logging
            import uuid
            import traceback
            from datetime import datetime
            from app.models.result import AssessmentResult
            logging.error(f"Background evaluation failed: {e}")
            with open("error_log.txt", "w") as f:
                f.write(traceback.format_exc())
            try:
                # Provide a fallback result so the frontend doesn't hang forever
                fallback = AssessmentResult(
                    id=str(uuid.uuid4()),
                    session_id=session_id,
                    total_score=0.0,
                    max_possible_score=100.0,
                    percentage=0.0,
                    passed=False,
                    per_question_scores=[],
                    strengths=[],
                    weaknesses=["System error occurred during evaluation."],
                    ai_feedback="An error occurred while analyzing the results. Please contact the administrator.",
                    evaluated_at=datetime.utcnow(),
                )
                db.add(fallback)
                
                # Update session status
                try:
                    res = await db.execute(select(AssessmentSession).where(AssessmentSession.id == session_id))
                    sess = res.scalar_one_or_none()
                    if sess:
                        sess.status = "evaluated"
                except Exception:
                    pass
                    
                await db.commit()
            except Exception as inner_e:
                logging.error(f"Failed to save fallback result: {inner_e}")

@router.post("/session/{session_id}/submit")
async def submit_assessment(
    session_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Submit assessment and trigger evaluation."""
    session = await assessment_service.get_session_by_id(db, session_id)
    session = await assessment_service.submit_session(db, session)

    # Run evaluation in background with a NEW db session
    background_tasks.add_task(_background_evaluate, session.id)

    return {
        "message": "Assessment submitted and evaluation started",
        "session_id": session.id,
        "status": "submitted",
    }


@router.get("/session/{session_id}/result", response_model=ResultOut)
async def get_result(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get the evaluation result for a submitted assessment."""
    session = await assessment_service.get_session_by_id(db, session_id)
    if session.status not in ("submitted", "evaluated"):
        raise HTTPException(status_code=400, detail="Assessment not yet submitted")

    result_r = await db.execute(
        select(AssessmentResult).where(AssessmentResult.session_id == session.id)
    )
    result = result_r.scalar_one_or_none()
    if not result:
        raise HTTPException(status_code=404, detail="Result not yet available. Please try again shortly.")

    out = ResultOut.model_validate(result)
    out.candidate_name = session.candidate_name
    out.candidate_email = session.candidate_email

    config = session.config
    tech_r = await db.execute(select(Technology).where(Technology.id == config.technology_id))
    tech = tech_r.scalar_one_or_none()

    out.assessment_title = config.title if config else None
    out.technology_name = tech.name if tech else None
    return out
