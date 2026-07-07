// Upload is at /upload (no /api prefix). All other routes are under /api.
const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function uploadSession(resume: File, jd: File, role: string) {
  const form = new FormData();
  form.append("resume_file", resume); // matches FastAPI: resume_file: UploadFile
  form.append("jd_file", jd);         // matches FastAPI: jd_file: UploadFile
  form.append("role", role);
  const res = await fetch(`${BASE}/upload`, { method: "POST", body: form });
  if (!res.ok) throw new Error(await res.text());
  return res.json(); // { session_id }
}

export async function generateQuestions(session_id: string) {
  const res = await fetch(`${BASE}/api/generate-questions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getQuestions(session_id: string) {
  const res = await fetch(`${BASE}/api/questions/${session_id}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function submitAnswer(
  session_id: string,
  question_id: string,
  answer_text: string,
  is_probe = false
) {
  const res = await fetch(`${BASE}/api/submit-answer`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id, question_id, answer_text, is_probe }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json(); // { evaluation, probe }
}

export async function summarizeSession(session_id: string) {
  const res = await fetch(`${BASE}/api/session/${session_id}/summarize`, {
    method: "POST",
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getSessionProgress(session_id: string) {
  const res = await fetch(`${BASE}/api/session/${session_id}/summary`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getAnalyticsSummary() {
  const res = await fetch(`${BASE}/api/analytics/summary`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
