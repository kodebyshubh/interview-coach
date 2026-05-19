from pydantic import BaseModel


class UploadResponse(BaseModel):
    session_id: str
    message: str
    resume_chunks: int
    jd_chunks: int


class RetrievalTestRequest(BaseModel):
    session_id: str
    query: str


class RetrievalTestResponse(BaseModel):
    session_id: str
    resume_chunks: list[str]
    jd_chunks: list[str]
