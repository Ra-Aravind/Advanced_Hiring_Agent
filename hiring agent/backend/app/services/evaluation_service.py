"""
Evaluation Service: auto-evaluates MCQ answers and calls AI for subjective ones.
"""
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from app.models.assessment import AssessmentSession, CandidateAnswer
from app.models.question import Question
from app.models.result import AssessmentResult
from app.models.technology import Technology
from app.services import ai_service
import logging

logger = logging.getLogger(__name__)


def _evaluate_mcq(question: Question, answer: CandidateAnswer) -> dict:
    """Auto-evaluate MCQ or true/false answer."""
    if answer.selected_option is None:
        return {"score": 0, "is_correct": False, "feedback": "No answer selected."}

    options = question.options or []
    if answer.selected_option < 0 or answer.selected_option >= len(options):
        return {"score": 0, "is_correct": False, "feedback": "Invalid option selected."}

    selected = options[answer.selected_option]
    is_correct = selected.get("is_correct", False)
    return {
        "score": question.max_score if is_correct else 0,
        "is_correct": is_correct,
        "feedback": question.explanation or ("Correct!" if is_correct else f"The correct answer is: {_get_correct_option_text(options)}"),
    }


def _get_correct_option_text(options: list) -> str:
    for opt in options:
        if opt.get("is_correct"):
            return f"{opt['label']}) {opt['text']}"
    return "See explanation."


async def evaluate_session(
    db: AsyncSession,
    session_id: str,
) -> AssessmentResult:
    """Evaluate all answers in a session and create/update the result."""
    # Load session with all relationships
    result = await db.execute(
        select(AssessmentSession)
        .where(AssessmentSession.id == session_id)
        .options(
            selectinload(AssessmentSession.config),
            selectinload(AssessmentSession.answers),
        )
    )
    session = result.scalar_one()
    config = session.config

    # Load technology
    tech_result = await db.execute(
        select(Technology).where(Technology.id == config.technology_id)
    )
    technology = tech_result.scalar_one()

    # Load all questions
    q_result = await db.execute(
        select(Question).where(Question.id.in_(session.question_ids))
    )
    questions = {q.id: q for q in q_result.scalars().all()}

    # Map answers
    answers_result = await db.execute(
        select(CandidateAnswer).where(CandidateAnswer.session_id == session_id)
    )
    answers = answers_result.scalars().all()
    answer_map = {a.question_id: a for a in answers}
    per_question_scores = []
    total_score = 0.0
    max_possible = 0.0

    for qid in session.question_ids:
        q = questions.get(qid)
        if not q:
            continue
        answer = answer_map.get(qid)
        max_possible += q.max_score

        if not answer:
            per_question_scores.append({
                "question_id": qid,
                "question_text": q.question_text,
                "question_type": q.question_type,
                "candidate_answer": None,
                "correct_answer": q.correct_answer,
                "score": 0,
                "max_score": q.max_score,
                "is_correct": False,
                "ai_feedback": "Not answered.",
            })
            continue

        if q.question_type in ("mcq", "true_false"):
            eval_result = _evaluate_mcq(q, answer)
        else:
            # AI evaluation for subjective/code
            eval_result = await ai_service.evaluate_subjective_answer(
                technology=technology.name,
                difficulty=q.difficulty,
                question=q.question_text,
                correct_answer=q.correct_answer or "",
                candidate_answer=answer.answer_text or "",
                max_score=q.max_score,
            )

        score = eval_result.get("score", 0)
        total_score += score

        per_question_scores.append({
            "question_id": qid,
            "question_text": q.question_text,
            "question_type": q.question_type,
            "candidate_answer": answer.answer_text or (
                str(answer.selected_option) if answer.selected_option is not None else None
            ),
            "correct_answer": q.correct_answer if q.question_type not in ("mcq", "true_false") else _get_correct_option_text(q.options or []),
            "score": score,
            "max_score": q.max_score,
            "is_correct": eval_result.get("is_correct", score > 0),
            "ai_feedback": eval_result.get("feedback", ""),
        })

    percentage = (total_score / max_possible * 100) if max_possible > 0 else 0
    passed = percentage >= config.passing_score

    # Generate narrative
    narrative = await ai_service.generate_result_narrative(
        technology=technology.name,
        percentage=percentage,
        total_score=total_score,
        max_score=max_possible,
        passed=passed,
        per_question_scores=per_question_scores,
    )

    # Check if result already exists (re-evaluation)
    existing_result = await db.execute(
        select(AssessmentResult).where(AssessmentResult.session_id == session.id)
    )
    assessment_result = existing_result.scalar_one_or_none()

    if assessment_result:
        assessment_result.total_score = total_score
        assessment_result.max_possible_score = max_possible
        assessment_result.percentage = percentage
        assessment_result.passed = passed
        assessment_result.per_question_scores = per_question_scores
        assessment_result.strengths = narrative.get("strengths", [])
        assessment_result.weaknesses = narrative.get("weaknesses", [])
        assessment_result.ai_feedback = narrative.get("ai_feedback", "")
        assessment_result.evaluated_at = datetime.utcnow()
    else:
        assessment_result = AssessmentResult(
            id=str(uuid.uuid4()),
            session_id=session.id,
            total_score=total_score,
            max_possible_score=max_possible,
            percentage=percentage,
            passed=passed,
            per_question_scores=per_question_scores,
            strengths=narrative.get("strengths", []),
            weaknesses=narrative.get("weaknesses", []),
            ai_feedback=narrative.get("ai_feedback", ""),
            evaluated_at=datetime.utcnow(),
        )
        db.add(assessment_result)

    # Update session status
    session.status = "evaluated"
    await db.flush()
    await db.commit()
    
    # ── Send Webhook to Phase 2 ────────────────────────────
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5.0) as client:
            webhook_payload = {
                "name": session.candidate_name,
                "email": session.candidate_email,
                "technology": technology.name,
                "score": round(percentage, 2),
                "status": "PASSED" if passed else "FAILED",
                "interview_eligible": passed
            }
            await client.post(
                "http://localhost:8000/api/v1/phase1/assessment-result",
                json=webhook_payload
            )
            logger.info(f"Webhook sent successfully for {session.candidate_email}")
    except Exception as e:
        logger.error(f"Failed to send webhook to Phase 2: {e}")
        
    return assessment_result
