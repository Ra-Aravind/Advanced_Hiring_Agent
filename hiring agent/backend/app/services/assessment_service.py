"""
Assessment Service: handles config creation, access code generation,
question selection, and session management.
"""
import random
import string
import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from app.models.assessment import AssessmentConfig, AssessmentSession, CandidateAnswer
from app.models.question import Question
from app.models.technology import Technology
from app.schemas.assessment import AssessmentConfigCreate, SessionStart
from fastapi import HTTPException


def generate_access_code(length: int = 8) -> str:
    """Generate a unique alphanumeric access code (e.g. PY-A3KX9Z)."""
    chars = string.ascii_uppercase + string.digits
    code = "".join(random.choices(chars, k=length))
    return f"{code[:2]}-{code[2:]}"


async def create_assessment_config(
    db: AsyncSession,
    data: AssessmentConfigCreate,
    created_by: str,
) -> AssessmentConfig:
    """Create an assessment config and select questions from the bank."""
    # Validate technology exists
    tech_result = await db.execute(
        select(Technology).where(Technology.id == data.technology_id)
    )
    tech = tech_result.scalar_one_or_none()
    if not tech:
        raise HTTPException(status_code=404, detail="Technology not found")

    # Select questions by difficulty
    mix = data.difficulty_mix
    selected_ids = []

    for difficulty, count in [
        ("beginner", mix.beginner),
        ("intermediate", mix.intermediate),
        ("advanced", mix.advanced),
    ]:
        if count <= 0:
            continue
        q_result = await db.execute(
            select(Question.id)
            .where(
                and_(
                    Question.technology_id == data.technology_id,
                    Question.difficulty == difficulty,
                    Question.is_active == True,
                )
            )
            .order_by(func.random())
            .limit(count)
        )
        ids = [row[0] for row in q_result.fetchall()]
        if len(ids) < count:
            raise HTTPException(
                status_code=422,
                detail=f"Not enough {difficulty} questions available. "
                       f"Need {count}, found {len(ids)}. Please add more questions.",
            )
        selected_ids.extend(ids)

    random.shuffle(selected_ids)

    # Generate unique access code for this config
    for _ in range(10):
        code = generate_access_code()
        existing = await db.execute(
            select(AssessmentConfig).where(AssessmentConfig.access_code == code)
        )
        if not existing.scalar_one_or_none():
            break

    config = AssessmentConfig(
        id=str(uuid.uuid4()),
        access_code=code,
        title=data.title,
        technology_id=data.technology_id,
        difficulty_mix=data.difficulty_mix.model_dump(),
        total_questions=data.total_questions,
        duration_minutes=data.duration_minutes,
        passing_score=data.passing_score,
        instructions=data.instructions,
        original_command=data.original_command,
        question_ids=selected_ids,
        created_by=created_by,
        is_active=True,
    )
    db.add(config)
    await db.flush()
    await db.commit()
    await db.refresh(config)
    return config


async def get_config_by_code(
    db: AsyncSession,
    access_code: str,
) -> AssessmentConfig:
    """Get an assessment config by its access code."""
    result = await db.execute(
        select(AssessmentConfig)
        .where(AssessmentConfig.access_code == access_code.upper())
    )
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="Invalid access code")
    if not config.is_active:
        raise HTTPException(status_code=400, detail="Assessment is no longer active")
    return config


async def get_session_by_id(
    db: AsyncSession,
    session_id: str,
) -> AssessmentSession:
    """Get a session by its unique UUID."""
    result = await db.execute(
        select(AssessmentSession)
        .where(AssessmentSession.id == session_id)
        .options(selectinload(AssessmentSession.config))
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


async def start_new_session(
    db: AsyncSession,
    config: AssessmentConfig,
    candidate_data: SessionStart,
) -> AssessmentSession:
    """Create a new session for a candidate taking this assessment."""
    now = datetime.utcnow()
    session = AssessmentSession(
        id=str(uuid.uuid4()),
        config_id=config.id,
        candidate_name=candidate_data.candidate_name,
        candidate_email=candidate_data.candidate_email,
        question_ids=config.question_ids,
        status="in_progress",
        started_at=now,
        created_at=now,
        expires_at=now + timedelta(minutes=config.duration_minutes),
    )
    db.add(session)
    await db.flush()
    await db.commit()
    
    # Reload with config so it can be used immediately
    result = await db.execute(
        select(AssessmentSession)
        .where(AssessmentSession.id == session.id)
        .options(selectinload(AssessmentSession.config))
    )
    return result.scalar_one()




async def save_answer(
    db: AsyncSession,
    session: AssessmentSession,
    question_id: str,
    answer_text: Optional[str],
    selected_option: Optional[int],
    time_spent_seconds: Optional[int],
):
    """Save or update a candidate's answer."""
    if session.status != "in_progress":
        raise HTTPException(status_code=400, detail="Session is not active")
    if session.expires_at and datetime.utcnow() > session.expires_at:
        raise HTTPException(status_code=400, detail="Assessment time has expired")

    # Check if answer already exists (update it)
    existing = await db.execute(
        select(CandidateAnswer).where(
            and_(
                CandidateAnswer.session_id == session.id,
                CandidateAnswer.question_id == question_id,
            )
        )
    )
    answer = existing.scalar_one_or_none()
    if answer:
        answer.answer_text = answer_text
        answer.selected_option = selected_option
        answer.time_spent_seconds = time_spent_seconds
        answer.answered_at = datetime.utcnow()
    else:
        answer = CandidateAnswer(
            id=str(uuid.uuid4()),
            session_id=session.id,
            question_id=question_id,
            answer_text=answer_text,
            selected_option=selected_option,
            time_spent_seconds=time_spent_seconds,
        )
        db.add(answer)
    await db.flush()
    await db.commit()


async def submit_session(
    db: AsyncSession,
    session: AssessmentSession,
) -> AssessmentSession:
    """Mark session as submitted for evaluation."""
    if session.status in ("submitted", "evaluated"):
        return session
    if session.status == "pending":
        raise HTTPException(status_code=400, detail="Assessment has not been started")
    session.status = "submitted"
    session.submitted_at = datetime.utcnow()
    await db.flush()
    await db.commit()
    return session


async def get_sanitized_questions(
    db: AsyncSession,
    question_ids: list,
) -> list[dict]:
    """Return questions without revealing correct answers."""
    if not question_ids:
        return []
    result = await db.execute(
        select(Question).where(Question.id.in_(question_ids))
    )
    questions = result.scalars().all()
    q_map = {q.id: q for q in questions}

    output = []
    for qid in question_ids:
        q = q_map.get(qid)
        if not q:
            continue
        q_dict = {
            "id": q.id,
            "question_text": q.question_text,
            "question_type": q.question_type,
            "difficulty": q.difficulty,
            "max_score": q.max_score,
        }
        # For MCQ: include options but remove is_correct flag
        if q.question_type in ("mcq", "true_false") and q.options:
            q_dict["options"] = [
                {"label": opt["label"], "text": opt["text"]}
                for opt in q.options
            ]
        output.append(q_dict)
    return output
