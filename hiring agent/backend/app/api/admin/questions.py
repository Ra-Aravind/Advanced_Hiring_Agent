from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
import uuid
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_admin
from app.models.question import Question
from app.models.technology import Technology
from app.models.user import User
from app.schemas.question import QuestionCreate, QuestionUpdate, QuestionOut, PaginatedQuestions, TechnologyOut

router = APIRouter(prefix="/api/admin/questions", tags=["Admin - Questions"])


@router.get("", response_model=PaginatedQuestions)
async def list_questions(
    technology_id: Optional[str] = Query(None),
    difficulty: Optional[str] = Query(None),
    question_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(True),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    filters = []
    if technology_id:
        filters.append(Question.technology_id == technology_id)
    if difficulty:
        filters.append(Question.difficulty == difficulty)
    if question_type:
        filters.append(Question.question_type == question_type)
    if is_active is not None:
        filters.append(Question.is_active == is_active)
    if search:
        filters.append(Question.question_text.ilike(f"%{search}%"))

    total_result = await db.execute(
        select(func.count(Question.id)).where(and_(*filters) if filters else True)
    )
    total = total_result.scalar()

    q_result = await db.execute(
        select(Question)
        .where(and_(*filters) if filters else True)
        .order_by(Question.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    questions = q_result.scalars().all()

    # Load technology names
    tech_ids = list({q.technology_id for q in questions})
    tech_result = await db.execute(select(Technology).where(Technology.id.in_(tech_ids)))
    tech_map = {t.id: t for t in tech_result.scalars().all()}

    items = []
    for q in questions:
        q_dict = QuestionOut.model_validate(q)
        if q.technology_id in tech_map:
            tech = tech_map[q.technology_id]
            q_dict.technology = TechnologyOut.model_validate(tech)
        items.append(q_dict)

    return PaginatedQuestions(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.post("", response_model=QuestionOut, status_code=201)
async def create_question(
    data: QuestionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    # Validate technology
    tech = await db.execute(select(Technology).where(Technology.id == data.technology_id))
    if not tech.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Technology not found")

    # Validate MCQ has options
    if data.question_type in ("mcq", "true_false") and not data.options:
        raise HTTPException(status_code=422, detail="MCQ/True-False questions must have options")

    options = [opt.model_dump() for opt in data.options] if data.options else None

    question = Question(
        id=str(uuid.uuid4()),
        technology_id=data.technology_id,
        question_type=data.question_type,
        difficulty=data.difficulty,
        question_text=data.question_text,
        options=options,
        correct_answer=data.correct_answer,
        explanation=data.explanation,
        max_score=data.max_score,
        tags=data.tags or [],
        source=data.source,
        created_by=current_user.id,
    )
    db.add(question)
    await db.flush()
    await db.commit()
    return QuestionOut.model_validate(question)


# NOTE: /technologies/list and /technologies MUST be defined BEFORE /{question_id}
# to avoid FastAPI treating "technologies" as a question_id
@router.get("/technologies/list", response_model=list[TechnologyOut])
async def list_technologies(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    result = await db.execute(select(Technology).where(Technology.is_active == True).order_by(Technology.name))
    return [TechnologyOut.model_validate(t) for t in result.scalars().all()]


@router.post("/technologies", response_model=TechnologyOut, status_code=201)
async def create_technology(
    name: str,
    slug: str,
    icon: Optional[str] = None,
    color: Optional[str] = None,
    description: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    existing = await db.execute(select(Technology).where(Technology.slug == slug))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Technology with this slug already exists")

    tech = Technology(
        id=str(uuid.uuid4()),
        name=name,
        slug=slug,
        icon=icon,
        color=color,
        description=description,
    )
    db.add(tech)
    await db.flush()
    await db.commit()
    return TechnologyOut.model_validate(tech)


@router.get("/{question_id}", response_model=QuestionOut)
async def get_question(
    question_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    result = await db.execute(select(Question).where(Question.id == question_id))
    question = result.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return QuestionOut.model_validate(question)


@router.put("/{question_id}", response_model=QuestionOut)
async def update_question(
    question_id: str,
    data: QuestionUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    result = await db.execute(select(Question).where(Question.id == question_id))
    question = result.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    update_data = data.model_dump(exclude_unset=True)
    if "options" in update_data and update_data["options"]:
        update_data["options"] = [opt.model_dump() if hasattr(opt, "model_dump") else opt for opt in update_data["options"]]

    for key, value in update_data.items():
        setattr(question, key, value)
    await db.flush()
    await db.commit()
    return QuestionOut.model_validate(question)


@router.delete("/{question_id}", status_code=204)
async def delete_question(
    question_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    result = await db.execute(select(Question).where(Question.id == question_id))
    question = result.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    question.is_active = False  # Soft delete
    await db.flush()
    await db.commit()
