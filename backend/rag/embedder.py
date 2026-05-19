import os
import uuid

import chromadb
from dotenv import load_dotenv

_client: chromadb.ClientAPI | None = None
_resume_collection = None
_jd_collection = None


def get_collections():
    global _client, _resume_collection, _jd_collection

    if _resume_collection is not None and _jd_collection is not None:
        return _resume_collection, _jd_collection

    load_dotenv()

    chroma_host = os.getenv("CHROMA_HOST")
    chroma_port = os.getenv("CHROMA_PORT")

    if not chroma_host or not chroma_port:
        raise RuntimeError("CHROMA_HOST and CHROMA_PORT must be set in the environment")

    _client = chromadb.HttpClient(host=chroma_host, port=int(chroma_port))

    _resume_collection = _client.get_or_create_collection(
        name="resume_chunks", metadata={"hnsw:space": "cosine"}
    )
    _jd_collection = _client.get_or_create_collection(
        name="jd_chunks", metadata={"hnsw:space": "cosine"}
    )

    return _resume_collection, _jd_collection


def _chunk_text(text: str, chunk_size: int = 400, overlap: int = 50) -> list[str]:
    text = text or ""
    chunks: list[str] = []

    step = max(1, chunk_size - overlap)
    start = 0

    while start < len(text):
        end = min(len(text), start + chunk_size)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += step

    return chunks


def embed_resume(session_id: str, text: str) -> int:
    chunks = _chunk_text(text)
    if not chunks:
        return 0

    resume_collection, _ = get_collections()

    resume_collection.add(
        ids=[f"{session_id}:resume:{uuid.uuid4()}" for _ in chunks],
        documents=chunks,
        metadatas=[{"session_id": session_id} for _ in chunks],
    )

    return len(chunks)


def embed_jd(session_id: str, text: str) -> int:
    chunks = _chunk_text(text)
    if not chunks:
        return 0

    _, jd_collection = get_collections()

    jd_collection.add(
        ids=[f"{session_id}:jd:{uuid.uuid4()}" for _ in chunks],
        documents=chunks,
        metadatas=[{"session_id": session_id} for _ in chunks],
    )

    return len(chunks)
