def create_pdf(filename, text):
    # Minimal PDF structure
    pdf_content = (
        b"%PDF-1.4\n"
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> >> >> /Contents 4 0 R >> endobj\n"
        b"4 0 obj << /Length " + str(len(text) + 50).encode() + b" >> stream\n"
        b"BT /F1 24 Tf 100 700 Td (" + text.encode('ascii', 'ignore') + b") Tj ET\n"
        b"endstream endobj\n"
        b"xref\n0 5\n0000000000 65535 f\n"
        b"0000000009 00000 n\n0000000058 00000 n\n0000000107 00000 n\n0000000250 00000 n\n"
        b"trailer << /Size 5 /Root 1 0 R >>\n"
        b"startxref\n320\n%%EOF"
    )
    with open(filename, 'wb') as f:
        f.write(pdf_content)

resume_text = "Experienced backend engineer with FastAPI, SQLAlchemy, Postgres, and RAG systems. Skilled in Python development and microservices architecture. Focuses on scalable solutions." * 3
jd_text = "Job requires building an AI interview coach using FastAPI, Postgres, and ChromaDB retrieval. Candidate should have experience with LLM integration and vector databases." * 3

create_pdf('resume.pdf', resume_text)
create_pdf('jd.pdf', jd_text)
