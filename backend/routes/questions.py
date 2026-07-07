import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from agents.question_generator import get_contexts, get_question_plan
from db.database import get_db
from db.models import EvalLog, Question, Session
from graph.build import graph

router = APIRouter()


class GenerateQuestionsRequest(BaseModel):
    session_id: str


@router.post("/generate-questions")
async def generate_questions(
    req: GenerateQuestionsRequest, db: AsyncSession = Depends(get_db)
):
    try:
        session_uuid = uuid.UUID(req.session_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="session_id must be a valid UUID") from e

    result = await db.execute(select(Session).where(Session.id == session_uuid))
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    count_result = await db.execute(
        select(func.count()).select_from(Question).where(Question.session_id == session_uuid)
    )
    if count_result.scalar() > 0:
        raise HTTPException(status_code=400, detail="Questions already generated for this session")

    resume_context, jd_context = get_contexts(req.session_id, session.role)

    try:
        result_state = graph.invoke({
            "stage": "generate_questions",
            "session_id": req.session_id,
            "role": session.role,
            "resume_context": resume_context,
            "jd_context": jd_context,
            "question_plan": get_question_plan(),
            "questions": [],
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM generation failed: {str(e)}") from e

    questions_data = result_state["questions"]
    log_entries = result_state.get("log_entries", [])

    saved = []
    for i, q in enumerate(questions_data):
        question = Question(
            id=uuid.uuid4(),
            session_id=session_uuid,
            text=q["question"],
            question_type=q["question_type"],
            expected_themes=q.get("expected_themes"),
            difficulty=q.get("difficulty"),
            order_index=i,
            source=q.get("source", "gemini"),
        )
        db.add(question)
        saved.append(question)

    # Questions must actually be flushed before EvalLog rows referencing their
    # ids — otherwise the FK insert can be ordered ahead of its parent and fail.
    await db.flush()

    # log entries are produced in the same order as questions_data — pair them
    # up so each generation call is attributed to the question it produced
    for log_entry, question in zip(log_entries, saved):
        db.add(EvalLog(
            id=uuid.uuid4(),
            session_id=session_uuid,
            question_id=question.id,
            question_text=log_entry["question_text"],
            answer_text=log_entry["answer_text"],
            score=log_entry["score"],
            latency_ms=log_entry["latency_ms"],
            model_used=log_entry["model_used"],
        ))

    await db.commit()

    return {
        "session_id": req.session_id,
        "questions_generated": len(saved),
        "questions": [
            {
                "id": str(q.id),
                "text": q.text,
                "question_type": q.question_type,
                "difficulty": q.difficulty,
                "order_index": q.order_index,
            }
            for q in saved
        ],
    }


@router.get("/questions/{session_id}")
async def get_questions(session_id: str, db: AsyncSession = Depends(get_db)):
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="session_id must be a valid UUID") from e

    session_check = await db.execute(select(Session).where(Session.id == session_uuid))
    if session_check.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Session not found")

    result = await db.execute(
        select(Question)
        .where(Question.session_id == session_uuid)
        .order_by(Question.order_index)
    )
    questions = result.scalars().all()

    return {
        "session_id": session_id,
        "questions": [
            {
                "id": str(q.id),
                "text": q.text,
                "question_type": q.question_type,
                "difficulty": q.difficulty,
                "expected_themes": q.expected_themes,
                "order_index": q.order_index,
                "source": q.source,
            }
            for q in questions
        ],
    }
