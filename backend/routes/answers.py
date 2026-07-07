import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from db.models import Answer, EvalLog, Question, Session
from graph.build import graph

router = APIRouter()


class SubmitAnswerRequest(BaseModel):
    session_id: str
    question_id: str
    answer_text: str
    is_probe: bool = False


@router.post("/submit-answer")
async def submit_answer(req: SubmitAnswerRequest, db: AsyncSession = Depends(get_db)):
    try:
        session_uuid = uuid.UUID(req.session_id)
        question_uuid = uuid.UUID(req.question_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="session_id and question_id must be valid UUIDs") from e

    session = await db.get(Session, session_uuid)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    question = await db.get(Question, question_uuid)
    if not question or question.session_id != session_uuid:
        raise HTTPException(status_code=404, detail="Question not found in this session")

    if not req.answer_text or len(req.answer_text.strip()) < 10:
        raise HTTPException(status_code=400, detail="Answer too short to evaluate")

    try:
        result_state = graph.invoke({
            "stage": "submit_answer",
            "question": {
                "text": question.text,
                "question_type": question.question_type,
                "expected_themes": question.expected_themes or [],
            },
            "answer_text": req.answer_text,
            "is_probe": req.is_probe,
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}") from e

    evaluation = result_state["evaluation"]
    probe = result_state.get("probe")

    answer = Answer(
        id=uuid.uuid4(),
        session_id=session_uuid,
        question_id=question_uuid,
        text=req.answer_text,
        score=evaluation["overall_score"],
        feedback=evaluation["feedback"],
        weak_topics=evaluation.get("weak_topics", []),
        is_probe=req.is_probe,
    )
    db.add(answer)

    for log_entry in result_state.get("log_entries", []):
        db.add(EvalLog(
            id=uuid.uuid4(),
            session_id=session_uuid,
            question_id=question_uuid,
            question_text=log_entry["question_text"],
            answer_text=log_entry["answer_text"],
            score=log_entry["score"],
            latency_ms=log_entry["latency_ms"],
            model_used=log_entry["model_used"],
        ))

    await db.commit()
    await db.refresh(answer)

    response_payload = {
        "answer_id": str(answer.id),
        "session_id": req.session_id,
        "question_id": req.question_id,
        "evaluation": {
            "scores": evaluation["scores"],
            "overall_score": evaluation["overall_score"],
            "feedback": evaluation["feedback"],
            "weak_topics": evaluation.get("weak_topics", []),
        },
        "probe": {
            "probe_question": probe["probe_question"],
            "targets": probe["targets"],
        } if probe else None,
    }

    return response_payload


@router.get("/answers/{session_id}")
async def get_session_answers(session_id: str, db: AsyncSession = Depends(get_db)):
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="session_id must be a valid UUID") from e

    result = await db.execute(
        select(Answer)
        .where(Answer.session_id == session_uuid)
        .order_by(Answer.created_at)
    )
    answers = result.scalars().all()

    if not answers:
        raise HTTPException(status_code=404, detail="No answers found for this session")

    return {
        "session_id": session_id,
        "total_answers": len(answers),
        "answers": [
            {
                "id": str(a.id),
                "question_id": str(a.question_id),
                "text": a.text,
                "score": a.score,
                "feedback": a.feedback,
                "weak_topics": a.weak_topics,
                "is_probe": a.is_probe,
                "created_at": a.created_at.isoformat(),
            }
            for a in answers
        ],
    }
