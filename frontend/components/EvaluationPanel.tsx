"use client";
import { motion } from "framer-motion";
import { ScoreBar } from "./ScoreBar";

type Props = {
  evaluation: {
    scores: Record<string, number>;
    overall_score: number;
    feedback: string;
    weak_topics: string[];
  };
};

export function EvaluationPanel({ evaluation }: Props) {
  const scoreColor =
    evaluation.overall_score >= 7 ? "text-accent"
    : evaluation.overall_score >= 5 ? "text-warn"
    : "text-danger";

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      className="panel-border bg-panel rounded-2xl overflow-hidden card-shadow"
    >
      {/* Score header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-border">
        <p className="font-mono text-[10px] text-dim uppercase tracking-[0.25em]">Evaluation</p>
        <span className={`font-serif text-3xl tnum ${scoreColor}`}>
          {evaluation.overall_score}
          <span className="text-base text-muted font-sans">/10</span>
        </span>
      </div>

      <div className="px-6 py-5 space-y-5">
        {/* Dimension bars */}
        <div className="space-y-3.5">
          {Object.entries(evaluation.scores).map(([dim, score]) => (
            <ScoreBar key={dim} label={dim} score={score} />
          ))}
        </div>

        {/* Feedback */}
        <p className="text-sm text-dim leading-relaxed border-t border-border pt-4">
          {evaluation.feedback}
        </p>

        {/* Weak topics */}
        {evaluation.weak_topics.length > 0 && (
          <div className="flex flex-wrap gap-2 border-t border-border pt-4">
            {evaluation.weak_topics.map((t) => (
              <span
                key={t}
                className="font-mono text-[10px] text-danger border border-danger/25
                  px-2.5 py-1 rounded-full tracking-wide"
              >
                {t}
              </span>
            ))}
          </div>
        )}
      </div>
    </motion.div>
  );
}
