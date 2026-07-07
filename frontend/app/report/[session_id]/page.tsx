"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { motion } from "framer-motion";
import { summarizeSession } from "@/lib/api";
import { ScoreBar } from "@/components/ScoreBar";

type Summary = {
  overall_score: number;
  performance_band: string;
  one_line_verdict: string;
  top_strengths: { topic: string; evidence: string }[];
  top_weaknesses: { topic: string; pattern: string; action: string }[];
  question_type_analysis: Record<string, string>;
  recommended_resources: { title: string; type: string; reason: string }[];
  computed_stats: {
    avg_score: number;
    type_breakdown: Record<string, number>;
    top_weak_topics: string[];
  };
};

const BAND_STYLES: Record<string, { color: string; bg: string }> = {
  poor:       { color: "text-danger", bg: "bg-danger/10 border-danger/30" },
  needs_work: { color: "text-warn",   bg: "bg-warn/10 border-warn/30" },
  decent:     { color: "text-warn",   bg: "bg-warn/10 border-warn/30" },
  strong:     { color: "text-accent", bg: "bg-accent/10 border-accent/30" },
  excellent:  { color: "text-accent", bg: "bg-accent/10 border-accent/30" },
};

function Section({ title, children, delay = 0 }: { title: string; children: React.ReactNode; delay?: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      className="panel-border bg-panel rounded-2xl p-6 card-shadow"
    >
      <p className="font-mono text-[10px] text-dim uppercase tracking-[0.3em] mb-5">{title}</p>
      {children}
    </motion.div>
  );
}

export default function ReportPage() {
  const { session_id } = useParams<{ session_id: string }>();
  const [summary, setSummary] = useState<Summary | null>(null);
  const [role, setRole] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    summarizeSession(session_id)
      .then((data) => {
        setSummary(data.summary);
        setRole(data.role);
        setLoading(false);
      })
      .catch((e: unknown) => {
        setError(e instanceof Error ? e.message : "Failed to load report.");
        setLoading(false);
      });
  }, [session_id]);

  if (loading) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4">
        <div
          className="w-48 h-px bg-border overflow-hidden rounded-full"
          style={{ position: "relative" }}
        >
          <motion.div
            className="absolute inset-y-0 left-0 bg-accent"
            animate={{ x: ["-100%", "200%"] }}
            transition={{ duration: 1.6, repeat: Infinity, ease: "easeInOut" }}
            style={{ width: "50%" }}
          />
        </div>
        <p className="font-serif text-2xl italic text-dim">Generating your report…</p>
        <p className="font-mono text-[10px] text-muted uppercase tracking-widest">This takes 10–15 seconds</p>
      </div>
    );
  }

  if (error || !summary) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="font-mono text-sm text-danger">{error || "Failed to load report."}</p>
      </div>
    );
  }

  const band = BAND_STYLES[summary.performance_band] || BAND_STYLES.decent;
  const scoreColor =
    summary.overall_score >= 7 ? "text-accent"
    : summary.overall_score >= 5 ? "text-warn"
    : "text-danger";

  return (
    <main className="min-h-screen px-4 py-16 max-w-2xl mx-auto space-y-5">

      {/* Score hero */}
      <motion.div
        initial={{ opacity: 0, y: -16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
        className="panel-border bg-panel rounded-2xl p-8 card-shadow"
      >
        <p className="font-mono text-[10px] text-dim uppercase tracking-[0.3em] mb-6">
          Interview Report — {role}
        </p>

        <div className="flex items-end gap-5 mb-5">
          <span className={`font-serif text-[5.5rem] leading-none tnum ${scoreColor}`}>
            {summary.overall_score}
          </span>
          <div className="mb-3 space-y-1.5">
            <span className={`font-mono text-[11px] uppercase tracking-[0.2em] px-3 py-1
              rounded-full border ${band.bg} ${band.color}`}>
              {summary.performance_band.replace("_", " ")}
            </span>
            <p className="font-mono text-[10px] text-muted">out of 10</p>
          </div>
        </div>

        <p className="text-dim text-sm italic leading-relaxed border-t border-border pt-5">
          &ldquo;{summary.one_line_verdict}&rdquo;
        </p>
      </motion.div>

      {/* Score by type */}
      <Section title="Score by Type" delay={0.1}>
        <div className="space-y-4">
          {Object.entries(summary.computed_stats.type_breakdown).map(([type, score]) => (
            <ScoreBar key={type} label={type.replace("_", " ")} score={score} />
          ))}
        </div>
      </Section>

      {/* Strengths */}
      <Section title="Strengths" delay={0.2}>
        <div className="space-y-4">
          {summary.top_strengths.map((s, i) => (
            <div key={s.topic} className="flex gap-4">
              <span className="font-mono text-[10px] text-accent/50 mt-0.5 shrink-0 tnum">
                0{i + 1}
              </span>
              <div>
                <p className="text-sm font-medium text-text">{s.topic}</p>
                <p className="text-xs text-dim mt-1 leading-relaxed">{s.evidence}</p>
              </div>
            </div>
          ))}
        </div>
      </Section>

      {/* Weaknesses */}
      <Section title="Areas to Fix" delay={0.3}>
        <div className="space-y-5">
          {summary.top_weaknesses.map((w) => (
            <div key={w.topic} className="pl-4 border-l border-danger/40 space-y-1">
              <p className="text-sm font-medium text-text">{w.topic}</p>
              <p className="text-xs text-dim leading-relaxed">{w.pattern}</p>
              <p className="text-xs text-accent font-mono mt-1.5">→ {w.action}</p>
            </div>
          ))}
        </div>
      </Section>

      {/* Resources */}
      <Section title="Recommended Resources" delay={0.4}>
        <div className="space-y-4">
          {summary.recommended_resources.map((r) => (
            <div key={r.title} className="flex gap-3 items-start">
              <span className="font-mono text-[9px] text-muted border border-border
                px-2 py-0.5 rounded mt-0.5 shrink-0 uppercase tracking-wider">
                {r.type}
              </span>
              <div>
                <p className="text-sm text-text">{r.title}</p>
                <p className="text-xs text-dim mt-0.5 leading-relaxed">{r.reason}</p>
              </div>
            </div>
          ))}
        </div>
      </Section>

      {/* Footer */}
      <div className="text-center py-6 pb-16">
        <a
          href="/"
          className="font-mono text-[10px] text-muted hover:text-dim transition-colors
            uppercase tracking-[0.3em]"
        >
          ← Start a new interview
        </a>
      </div>
    </main>
  );
}
