"use client";
import { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { uploadSession, generateQuestions } from "@/lib/api";

export default function Home() {
  const router = useRouter();
  const [role, setRole] = useState("");
  const [resume, setResume] = useState<File | null>(null);
  const [jd, setJd] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const resumeRef = useRef<HTMLInputElement>(null);
  const jdRef = useRef<HTMLInputElement>(null);

  async function handleStart() {
    if (!resume || !jd || !role.trim()) {
      setError("All three fields required.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const { session_id } = await uploadSession(resume, jd, role);
      await generateQuestions(session_id);
      router.push(`/interview/${session_id}`);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Something went wrong.");
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen flex flex-col items-center justify-center px-6 py-20 relative overflow-hidden">
      {/* Background radial glow */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background:
            "radial-gradient(ellipse 70% 50% at 50% 40%, rgba(200,165,58,0.055) 0%, transparent 70%)",
        }}
      />

      {/* Hero */}
      <motion.div
        initial={{ opacity: 0, y: -24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.9, ease: [0.16, 1, 0.3, 1] }}
        className="text-center mb-14 relative z-10"
      >
        <p className="font-mono text-[10px] text-accent tracking-[0.45em] mb-8 uppercase">
          Intelligence · Assessment · Forge
        </p>

        <h1 className="font-serif leading-[0.88] tracking-tight">
          <span className="block text-[5.5rem] md:text-[8.5rem] text-text">Interview</span>
          <span className="block text-[5.5rem] md:text-[8.5rem] italic text-accent">Forge</span>
        </h1>

        <div className="flex items-center justify-center gap-4 mt-7 mb-6">
          <div className="h-px w-12 bg-border" />
          <div className="w-1 h-1 rounded-full bg-accent/60" />
          <div className="h-px w-12 bg-border" />
        </div>

        <p className="text-dim text-base max-w-xs mx-auto leading-relaxed">
          Upload your resume and a job description. A tailored interview begins.
        </p>
      </motion.div>

      {/* Form */}
      <motion.div
        initial={{ opacity: 0, y: 32 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.9, delay: 0.18, ease: [0.16, 1, 0.3, 1] }}
        className="w-full max-w-md space-y-3 relative z-10"
      >
        {/* Role */}
        <div>
          <label className="font-mono text-[10px] text-dim uppercase tracking-[0.22em] block mb-1.5">
            Role applying for
          </label>
          <input
            type="text"
            placeholder="e.g. Backend Engineer, ML Engineer…"
            value={role}
            onChange={(e) => setRole(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleStart()}
            className="w-full bg-panel panel-border rounded-lg px-4 py-3 text-text
              placeholder-muted text-sm outline-none font-sans transition-colors
              focus:border-accent/40 focus:bg-elevated"
          />
        </div>

        {/* File uploads */}
        {[
          { label: "Resume", file: resume, set: setResume, ref: resumeRef },
          { label: "Job Description", file: jd, set: setJd, ref: jdRef },
        ].map(({ label, file, set, ref }) => (
          <div key={label}>
            <label className="font-mono text-[10px] text-dim uppercase tracking-[0.22em] block mb-1.5">
              {label}
            </label>
            <button
              onClick={() => ref.current?.click()}
              className={`w-full rounded-lg px-4 py-3 flex items-center gap-3 text-sm
                transition-all border border-dashed text-left ${
                  file
                    ? "border-accent/50 bg-accent/5 text-accent"
                    : "border-border text-dim hover:border-muted hover:text-text"
                }`}
            >
              <span className="font-mono text-xs w-4 shrink-0">{file ? "✓" : "+"}</span>
              <span className="truncate">{file ? file.name : `Upload ${label} — PDF`}</span>
            </button>
            <input
              ref={ref}
              type="file"
              accept=".pdf"
              className="hidden"
              onChange={(e) => set(e.target.files?.[0] || null)}
            />
          </div>
        ))}

        {error && (
          <p className="font-mono text-[11px] text-danger pt-1">{error}</p>
        )}

        <div className="pt-1">
          <button
            onClick={handleStart}
            disabled={loading}
            className="w-full bg-accent text-surface font-mono text-sm font-bold
              tracking-[0.22em] uppercase py-4 rounded-lg transition-all
              hover:bg-accent/90 active:scale-[0.99] disabled:opacity-40
              disabled:cursor-not-allowed accent-glow"
          >
            {loading ? "Preparing Session…" : "Begin Assessment →"}
          </button>
        </div>
      </motion.div>

      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.9 }}
        className="text-muted font-mono text-[10px] mt-10 tracking-[0.35em] uppercase relative z-10"
      >
        8 questions · adaptive evaluation · full report
      </motion.p>
    </main>
  );
}
