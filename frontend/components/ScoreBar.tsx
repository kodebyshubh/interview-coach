"use client";
import { motion } from "framer-motion";

type Props = { label: string; score: number };

export function ScoreBar({ label, score }: Props) {
  const color =
    score >= 7 ? "#c8a53a"
    : score >= 5 ? "#e08030"
    : "#e05252";

  return (
    <div className="space-y-1.5">
      <div className="flex justify-between items-baseline">
        <span className="font-sans text-xs text-dim capitalize">{label}</span>
        <span className="font-mono text-xs tnum" style={{ color }}>
          {typeof score === "number" ? score.toFixed(1) : score}
        </span>
      </div>
      <div className="h-px bg-border rounded-full overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${(score / 10) * 100}%` }}
          transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
          className="h-full rounded-full"
          style={{ backgroundColor: color }}
        />
      </div>
    </div>
  );
}
