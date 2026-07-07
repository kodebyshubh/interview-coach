"use client";
import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { getAnalyticsSummary } from "@/lib/api";
import { ScoreBar } from "@/components/ScoreBar";

type Summary = {
  score_over_time: { session_id: string; created_at: string; avg_score: number }[];
  latency_by_model: { model_used: string; avg_latency_ms: number; call_count: number }[];
  score_by_question_type: { question_type: string; avg_score: number; answer_count: number }[];
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

function LatencyBar({ label, ms, maxMs, count }: { label: string; ms: number; maxMs: number; count: number }) {
  return (
    <div className="space-y-1.5">
      <div className="flex justify-between items-baseline">
        <span className="font-sans text-xs text-dim capitalize">{label}</span>
        <span className="font-mono text-xs tnum text-accent">
          {ms.toFixed(0)}ms <span className="text-muted">({count} calls)</span>
        </span>
      </div>
      <div className="h-px bg-border rounded-full overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${(ms / maxMs) * 100}%` }}
          transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
          className="h-full rounded-full bg-accent"
        />
      </div>
    </div>
  );
}

export default function AnalyticsPage() {
  const [data, setData] = useState<Summary | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getAnalyticsSummary()
      .then((d) => {
        setData(d);
        setLoading(false);
      })
      .catch((e: unknown) => {
        setError(e instanceof Error ? e.message : "Failed to load analytics.");
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="font-serif text-2xl italic text-dim">Loading analytics…</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="font-mono text-sm text-danger">{error || "Failed to load analytics."}</p>
      </div>
    );
  }

  const maxLatency = Math.max(...data.latency_by_model.map((m) => m.avg_latency_ms), 1);

  return (
    <main className="min-h-screen px-4 py-16 max-w-2xl mx-auto space-y-5">
      <motion.div
        initial={{ opacity: 0, y: -16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
        className="panel-border bg-panel rounded-2xl p-8 card-shadow"
      >
        <p className="font-mono text-[10px] text-dim uppercase tracking-[0.3em] mb-2">
          Eval Log Analytics
        </p>
        <p className="text-dim text-sm italic">
          Aggregated from every LLM call logged through the graph.
        </p>
      </motion.div>

      <Section title="Average Score Over Time (by session)" delay={0.1}>
        {data.score_over_time.length === 0 ? (
          <p className="text-xs text-dim">No scored sessions yet.</p>
        ) : (
          <div className="space-y-3">
            {data.score_over_time.map((point) => (
              <div key={point.session_id} className="flex justify-between items-baseline">
                <span className="font-mono text-xs text-dim">
                  {new Date(point.created_at).toLocaleString()}
                </span>
                <span className="font-mono text-xs text-muted">
                  {point.session_id.slice(0, 8)}…
                </span>
                <ScoreBarInline score={point.avg_score} />
              </div>
            ))}
          </div>
        )}
      </Section>

      <Section title="Average Latency by Model" delay={0.2}>
        {data.latency_by_model.length === 0 ? (
          <p className="text-xs text-dim">No LLM calls logged yet.</p>
        ) : (
          <div className="space-y-4">
            {data.latency_by_model.map((m) => (
              <LatencyBar
                key={m.model_used}
                label={m.model_used}
                ms={m.avg_latency_ms}
                maxMs={maxLatency}
                count={m.call_count}
              />
            ))}
          </div>
        )}
      </Section>

      <Section title="Average Score by Question Type" delay={0.3}>
        {data.score_by_question_type.length === 0 ? (
          <p className="text-xs text-dim">No evaluated answers yet.</p>
        ) : (
          <div className="space-y-4">
            {data.score_by_question_type.map((t) => (
              <ScoreBar
                key={t.question_type}
                label={`${t.question_type.replace("_", " ")} (${t.answer_count})`}
                score={t.avg_score}
              />
            ))}
          </div>
        )}
      </Section>

      <div className="text-center py-6 pb-16">
        <a
          href="/"
          className="font-mono text-[10px] text-muted hover:text-dim transition-colors
            uppercase tracking-[0.3em]"
        >
          ← Back to home
        </a>
      </div>
    </main>
  );
}

function ScoreBarInline({ score }: { score: number }) {
  const color = score >= 7 ? "text-accent" : score >= 5 ? "text-warn" : "text-danger";
  return <span className={`font-mono text-xs tnum ${color}`}>{score.toFixed(1)}</span>;
}
