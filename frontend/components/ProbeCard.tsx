"use client";
import { motion } from "framer-motion";

type Props = {
  probe: { probe_question: string; targets: string };
  answer: string;
  onChange: (v: string) => void;
  onSubmit: () => void;
  submitting: boolean;
};

export function ProbeCard({ probe, answer, onChange, onSubmit, submitting }: Props) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      className="rounded-2xl overflow-hidden"
      style={{
        border: "1px solid rgba(224, 128, 48, 0.25)",
        background: "rgba(224, 128, 48, 0.04)",
      }}
    >
      {/* Header */}
      <div className="flex items-center gap-3 px-6 py-4 border-b"
        style={{ borderColor: "rgba(224, 128, 48, 0.15)" }}>
        <span className="font-mono text-[10px] text-warn uppercase tracking-[0.25em]">Follow-up</span>
        <span className="text-muted">·</span>
        <span className="font-sans text-[11px] text-dim truncate">{probe.targets}</span>
      </div>

      <div className="px-6 py-5 space-y-4">
        <p className="font-serif text-[1.5rem] leading-[1.35] text-text">{probe.probe_question}</p>
        <textarea
          value={answer}
          onChange={(e) => onChange(e.target.value)}
          placeholder="Take another shot at this…"
          rows={5}
          className="w-full bg-surface rounded-xl p-4 text-text text-sm placeholder-muted
            outline-none resize-none font-sans leading-relaxed transition-colors"
          style={{ border: "1px solid rgba(224, 128, 48, 0.2)" }}
        />
        <button
          onClick={onSubmit}
          disabled={submitting || answer.trim().length < 10}
          className="w-full font-mono text-sm uppercase tracking-[0.2em] py-3.5 rounded-lg
            transition-all disabled:opacity-40 disabled:cursor-not-allowed"
          style={{
            border: "1px solid rgba(224, 128, 48, 0.4)",
            color: "#e08030",
            background: submitting ? "rgba(224,128,48,0.08)" : "transparent",
          }}
          onMouseEnter={(e) => { (e.currentTarget.style.background = "rgba(224,128,48,0.08)"); }}
          onMouseLeave={(e) => { if (!submitting) e.currentTarget.style.background = "transparent"; }}
        >
          {submitting ? "Submitting…" : "Submit Follow-up →"}
        </button>
      </div>
    </motion.div>
  );
}
