from .embedder import get_collections


def retrieve_resume_context(session_id: str, query: str, n: int = 3) -> list[str]:
    resume_collection, _ = get_collections()
    result = resume_collection.query(
        query_texts=[query],
        n_results=n,
        where={"session_id": session_id},
        include=["documents"],
    )

    documents = result.get("documents") or []
    if not documents:
        return []

    return documents[0] or []


def retrieve_jd_context(session_id: str, query: str, n: int = 3) -> list[str]:
    _, jd_collection = get_collections()
    result = jd_collection.query(
        query_texts=[query],
        n_results=n,
        where={"session_id": session_id},
        include=["documents"],
    )

    documents = result.get("documents") or []
    if not documents:
        return []

    return documents[0] or []
