def make_pdf(name, txt):
    content = f"%PDF-1.1\n1 0 obj <</Type/Catalog/Pages 2 0 R>> endobj\n2 0 obj <</Type/Pages/Kids [3 0 R]/Count 1>> endobj\n3 0 obj <</Type/Page/Parent 2 0 R/MediaBox [0 0 600 800]/Resources <</Font <</F1 <</Type/Font/Subtype/Type1/BaseFont/Helvetica>>>>>>/Contents 4 0 R>> endobj\n4 0 obj <</Length {len(txt)+20}>> stream\nBT /F1 12 Tf 50 700 Td ({txt}) Tj ET\nendstream endobj\nxref\n0 5\n0000000000 65535 f\n0000000009 00000 n\n0000000052 00000 n\n0000000101 00000 n\n0000000215 00000 n\ntrailer <</Size 5/Root 1 0 R>>\nstartxref\n300\n%%EOF".encode("ascii", "ignore")
    with open(name, 'wb') as f: f.write(content)

tx = "This document is long enough to have more than one hundred characters. Indeed, we need to ensure the processing logic can successfully chunk this text into vector database records."
make_pdf('resume.pdf', tx)
make_pdf('jd.pdf', tx)
