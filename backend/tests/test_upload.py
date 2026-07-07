from unittest.mock import patch

import pytest
from sqlalchemy import select

from db.models import Session as InterviewSession


FAKE_PDF = b"%PDF-1.4 fake"


@pytest.mark.parametrize("missing_field", ["role", "resume_file", "jd_file"])
async def test_upload_missing_field(client, missing_field):
    data = {"role": "Backend Engineer"}
    files = {
        "resume_file": ("r.pdf", FAKE_PDF, "application/pdf"),
        "jd_file": ("j.pdf", FAKE_PDF, "application/pdf"),
    }
    if missing_field == "role":
        data.pop("role")
    else:
        files.pop(missing_field)

    with patch("main.extract_text_from_pdf", return_value="text"), \
         patch("main.embed_resume", return_value=3), \
         patch("main.embed_jd", return_value=3):
        response = await client.post("/upload", data=data, files=files)

    assert response.status_code == 422


async def test_upload_valid_pdf_files(client):
    with patch("main.extract_text_from_pdf", return_value="resume content"), \
         patch("main.embed_resume", return_value=5), \
         patch("main.embed_jd", return_value=4):
        response = await client.post(
            "/upload",
            data={"role": "Backend Engineer"},
            files={
                "resume_file": ("resume.pdf", FAKE_PDF, "application/pdf"),
                "jd_file": ("jd.pdf", FAKE_PDF, "application/pdf"),
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data


async def test_upload_creates_session_in_db(client, db):
    with patch("main.extract_text_from_pdf", return_value="resume content"), \
         patch("main.embed_resume", return_value=5), \
         patch("main.embed_jd", return_value=4):
        response = await client.post(
            "/upload",
            data={"role": "Data Engineer"},
            files={
                "resume_file": ("resume.pdf", FAKE_PDF, "application/pdf"),
                "jd_file": ("jd.pdf", FAKE_PDF, "application/pdf"),
            },
        )

    assert response.status_code == 200
    session_id = response.json()["session_id"]

    import uuid as _uuid
    result = await db.execute(
        select(InterviewSession).where(InterviewSession.id == _uuid.UUID(session_id))
    )
    session = result.scalar_one_or_none()
    assert session is not None
    assert session.role == "Data Engineer"
