import chromadb
client = chromadb.HttpClient(host='localhost', port=8001)
sid = '60d47e65-2481-43c6-a0b3-a7110ef3a138'
try:
    resume_col = client.get_collection('resume_chunks')
    jd_col = client.get_collection('jd_chunks')
    r_count = len(resume_col.get(where={'session_id': sid})['ids'])
    j_count = len(jd_col.get(where={'session_id': sid})['ids'])
    print(f"Counts: resume={r_count}, jd={j_count}")
except Exception as e:
    print(f"Chroma Error: {e}")
