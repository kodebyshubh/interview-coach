import chromadb
try:
    c = chromadb.HttpClient(host='localhost', port=8001)
    sid = '5177decc-8f2c-496d-b32b-61d9f834a054'
    r = c.get_collection('resume_chunks').get(where={'session_id': sid})
    j = c.get_collection('jd_chunks').get(where={'session_id': sid})
    print(f"resume_docs: {len(r['ids'])}")
    print(f"jd_docs: {len(j['ids'])}")
except Exception as e:
    print(f"Query Error: {e}")
