import chromadb
import sys

sid = 'e1e928c9-42c4-410a-aff5-c93f99d69825'
try:
    c = chromadb.HttpClient(host='localhost', port=8001)
    rc = c.get_collection('resume_chunks')
    jc = c.get_collection('jd_chunks')
    r = rc.get(where={'session_id': sid})
    j = jc.get(where={'session_id': sid})
    print(f"resume_docs: {len(r.get('documents', []))}")
    print(f"jd_docs: {len(j.get('documents', []))}")
except Exception as e:
    print(f"Error: {e}")
