from contextlib import asynccontextmanager
import uuid

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from db.init_db import init_db
from db.models import Session
from rag.embedder import embed_jd, embed_resume
from rag.retriever import retrieve_jd_context, retrieve_resume_context
from schemas import RetrievalTestRequest, RetrievalTestResponse, UploadResponse
from utils.pdf_parser import extract_text_from_pdf


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/health/db")
async def health_db(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        return {"db": "ok"}
    except Exception as e:
        return {"db": "error", "detail": str(e)}


@app.post("/upload", response_model=UploadResponse)
async def upload(
    role: str = Form(...),
    resume_file: UploadFile = File(...),
    jd_file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    session_uuid = uuid.uuid4()
    session_id = str(session_uuid)

    resume_bytes = await resume_file.read()
    jd_bytes = await jd_file.read()

    try:
        resume_text = extract_text_from_pdf(resume_bytes)
        jd_text = extract_text_from_pdf(jd_bytes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    jd_summary = (jd_text or "")[:300]

    await db.merge(Session(id=session_uuid, role=role, jd_summary=jd_summary))
    await db.commit()

    resume_chunks = embed_resume(session_id, resume_text)
    jd_chunks = embed_jd(session_id, jd_text)

    return UploadResponse(
        session_id=session_id,
        message="uploaded",
        resume_chunks=resume_chunks,
        jd_chunks=jd_chunks,
    )


@app.post("/debug/retrieve", response_model=RetrievalTestResponse)
async def debug_retrieve(payload: RetrievalTestRequest):
    resume_chunks = retrieve_resume_context(payload.session_id, payload.query, n=3)
    jd_chunks = retrieve_jd_context(payload.session_id, payload.query, n=3)
    return RetrievalTestResponse(
        session_id=payload.session_id,
        resume_chunks=resume_chunks,
        jd_chunks=jd_chunks,
    )


@app.get("/debug/session/{session_id}")
async def debug_session(session_id: str, db: AsyncSession = Depends(get_db)):
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="session_id must be a UUID string") from e

    result = await db.execute(select(Session).where(Session.id == session_uuid))
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "id": str(session.id),
        "created_at": session.created_at.isoformat() if session.created_at else None,
        "role": session.role,
        "jd_summary": session.jd_summary,
        "status": session.status,
    }
