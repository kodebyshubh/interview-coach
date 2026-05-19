import chromadb
try:
    c = chromadb.HttpClient(host='localhost', port=8001)
    sid = '8817e2cd-484a-44c3-9909-d8ef65857267'
    r = c.get_collection('resume_chunks').get(where={'session_id': sid})
    j = c.get_collection('jd_chunks').get(where={'session_id': sid})
    print(f"resume_docs: {len(r['ids'])}")
    print(f"jd_docs: {len(j['ids'])}")
except Exception as e:
    print(f"Query Error: {e}")
