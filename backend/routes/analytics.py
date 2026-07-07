from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from db.models import EvalLog, Question, Session

router = APIRouter()


@router.get("/analytics/summary")
async def analytics_summary(db: AsyncSession = Depends(get_db)):
    # Average score over time, one point per session (ordered by when the session
    # was created) — most live-tested data lands on the same day, so per-session
    # granularity is more informative here than a daily bucket would be.
    score_over_time_result = await db.execute(
        select(
            Session.id,
            Session.created_at,
            func.avg(EvalLog.score),
        )
        .join(EvalLog, EvalLog.session_id == Session.id)
        .where(EvalLog.score.is_not(None))
        .group_by(Session.id, Session.created_at)
        .order_by(Session.created_at)
    )
    score_over_time = [
        {
            "session_id": str(session_id),
            "created_at": created_at.isoformat(),
            "avg_score": round(float(avg_score), 2),
        }
        for session_id, created_at, avg_score in score_over_time_result.all()
    ]

    # Average latency and call volume by which model actually served the call.
    latency_by_model_result = await db.execute(
        select(
            EvalLog.model_used,
            func.avg(EvalLog.latency_ms),
            func.count(),
        ).group_by(EvalLog.model_used)
    )
    latency_by_model = [
        {
            "model_used": model_used,
            "avg_latency_ms": round(float(avg_latency), 1),
            "call_count": count,
        }
        for model_used, avg_latency, count in latency_by_model_result.all()
    ]

    # Average score by question_type — joins eval_logs to questions since eval_logs
    # itself has no question_type column; only scored (evaluation) rows count here.
    score_by_type_result = await db.execute(
        select(
            Question.question_type,
            func.avg(EvalLog.score),
            func.count(),
        )
        .join(Question, Question.id == EvalLog.question_id)
        .where(EvalLog.score.is_not(None))
        .group_by(Question.question_type)
    )
    score_by_question_type = [
        {
            "question_type": question_type,
            "avg_score": round(float(avg_score), 2),
            "answer_count": count,
        }
        for question_type, avg_score, count in score_by_type_result.all()
    ]

    return {
        "score_over_time": score_over_time,
        "latency_by_model": latency_by_model,
        "score_by_question_type": score_by_question_type,
    }
