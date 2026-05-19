from __future__ import annotations

from io import BytesIO

from PyPDF2 import PdfReader


def extract_text_from_pdf(file_bytes: bytes) -> str:
    reader = PdfReader(BytesIO(file_bytes))

    texts: list[str] = []
    for page in reader.pages:
        page_text = page.extract_text() or ""
        if page_text:
            texts.append(page_text)

    text = "\n".join(texts).strip()

    # Light whitespace normalization
    text = "\n".join(line.strip() for line in text.splitlines()).strip()

    if len(text) < 50:
        raise ValueError("PDF appears to be empty or scanned")

    return text
