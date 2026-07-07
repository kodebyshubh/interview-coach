import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from db.models import Answer, EvalLog, Question, Session
from graph.build import graph

router = APIRouter()


@router.post("/session/{session_id}/summarize")
async def summarize_session(session_id: str, db: AsyncSession = Depends(get_db)):
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid session_id format") from e

    session = await db.get(Session, session_uuid)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    result = await db.execute(
        select(Answer, Question)
        .join(Question, Answer.question_id == Question.id)
        .where(Answer.session_id == session_uuid)
        .where(Answer.is_probe == False)  # noqa: E712
        .order_by(Answer.created_at)
    )
    rows = result.all()

    if not rows:
        raise HTTPException(status_code=400, detail="No answers found — complete the interview first")

    if len(rows) < 3:
        raise HTTPException(
            status_code=400,
            detail=f"Only {len(rows)} answers submitted — need at least 3 to summarize",
        )

    answers_payload = [
        {
            "question_text": q.text,
            "question_type": q.question_type,
            "answer_text": a.text,
            "score": a.score,
            "feedback": a.feedback,
            "weak_topics": a.weak_topics or [],
        }
        for a, q in rows
    ]

    try:
        result_state = graph.invoke({
            "stage": "summarize",
            "role": session.role,
            "answers": answers_payload,
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summary generation failed: {str(e)}") from e

    summary = result_state["summary"]

    for log_entry in result_state.get("log_entries", []):
        db.add(EvalLog(
            id=uuid.uuid4(),
            session_id=session_uuid,
            question_id=None,
            question_text=log_entry["question_text"],
            answer_text=log_entry["answer_text"],
            score=log_entry["score"],
            latency_ms=log_entry["latency_ms"],
            model_used=log_entry["model_used"],
        ))
    await db.commit()

    return {
        "session_id": session_id,
        "role": session.role,
        "summary": summary,
    }


@router.get("/session/{session_id}/summary")
async def get_session_summary(session_id: str, db: AsyncSession = Depends(get_db)):
    """Cheap progress check — raw scores only, no LLM call."""
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid session_id format") from e

    result = await db.execute(
        select(Answer)
        .where(Answer.session_id == session_uuid)
        .order_by(Answer.created_at)
    )
    answers = result.scalars().all()

    if not answers:
        raise HTTPException(status_code=404, detail="No answers found")

    scores = [a.score for a in answers if a.score is not None]
    avg = round(sum(scores) / len(scores), 1) if scores else 0

    return {
        "session_id": session_id,
        "answers_submitted": len(answers),
        "average_score": avg,
        "scores": [
            {
                "question_id": str(a.question_id),
                "score": a.score,
                "is_probe": a.is_probe,
            }
            for a in answers
        ],
    }
