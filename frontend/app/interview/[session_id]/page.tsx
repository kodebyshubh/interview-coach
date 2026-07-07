"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { getQuestions, submitAnswer } from "@/lib/api";
import { EvaluationPanel } from "@/components/EvaluationPanel";
import { ProbeCard } from "@/components/ProbeCard";

type Question = {
  id: string;
  text: string;
  question_type: string;
  difficulty: string;
  order_index: number;
};

type Evaluation = {
  scores: Record<string, number>;
  overall_score: number;
  feedback: string;
  weak_topics: string[];
};

type Probe = {
  probe_question: string;
  targets: string;
};

type AnswerState = {
  evaluation: Evaluation;
  probe: Probe | null;
  probeAnswered: boolean;
};

const TYPE_LABELS: Record<string, string> = {
  behavioral: "Behavioral",
  technical: "Technical",
  situational: "Situational",
  resume_deep_dive: "Resume Deep Dive",
};

const DIFF_COLORS: Record<string, string> = {
  easy: "text-accent",
  medium: "text-warn",
  hard: "text-danger",
};

export default function InterviewPage() {
  const { session_id } = useParams<{ session_id: string }>();
  const router = useRouter();

  const [questions, setQuestions] = useState<Question[]>([]);
  const [current, setCurrent] = useState(0);
  const [answer, setAnswer] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [answerStates, setAnswerStates] = useState<Record<string, AnswerState>>({});
  const [probeAnswer, setProbeAnswer] = useState("");
  const [submittingProbe, setSubmittingProbe] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getQuestions(session_id)
      .then((data) => {
        const sorted = [...data.questions].sort(
          (a: Question, b: Question) => a.order_index - b.order_index
        );
        setQuestions(sorted);
        setLoading(false);
      })
      .catch(console.error);
  }, [session_id]);

  const currentQ = questions[current];
  const currentState = currentQ ? answerStates[currentQ.id] : null;
  const allAnswered =
    questions.length > 0 &&
    questions.every((q) => answerStates[q.id]?.probeAnswered === true);

  async function handleSubmit() {
    if (!answer.trim() || !currentQ) return;
    setSubmitting(true);
    try {
      const result = await submitAnswer(session_id, currentQ.id, answer, false);
      setAnswerStates((prev) => ({
        ...prev,
        [currentQ.id]: {
          evaluation: result.evaluation,
          probe: result.probe,
          probeAnswered: result.probe ? false : true,
        },
      }));
    } finally {
      setSubmitting(false);
    }
  }

  async function handleProbeSubmit() {
    if (!probeAnswer.trim() || !currentQ) return;
    setSubmittingProbe(true);
    try {
      await submitAnswer(session_id, currentQ.id, probeAnswer, true);
      setAnswerStates((prev) => ({
        ...prev,
        [currentQ.id]: { ...prev[currentQ.id], probeAnswered: true },
      }));
      setProbeAnswer("");
    } finally {
      setSubmittingProbe(false);
    }
  }

  function handleNext() {
    setAnswer("");
    setCurrent((c) => c + 1);
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-3">
          <p className="font-serif text-2xl italic text-dim animate-pulse">Loading questions…</p>
          <p className="font-mono text-[10px] text-muted uppercase tracking-widest">Preparing your session</p>
        </div>
      </div>
    );
  }

  const answeredCount = Object.values(answerStates).filter((s) => s.probeAnswered).length;
  const progressPct = questions.length > 0 ? (answeredCount / questions.length) * 100 : 0;

  return (
    <main className="min-h-screen px-4 py-10 max-w-2xl mx-auto">
      {/* Header bar */}
      <div className="flex items-center justify-between mb-2">
        <p className="font-mono text-[10px] text-dim uppercase tracking-[0.3em]">InterviewForge</p>
        <p className="font-mono text-[10px] text-dim">
          <span className="text-text tnum">{answeredCount}</span>
          <span className="text-muted"> / {questions.length}</span>
        </p>
      </div>

      {/* Progress bar */}
      <div className="h-px bg-border mb-10 overflow-hidden rounded-full">
        <motion.div
          className="h-full bg-accent rounded-full"
          initial={{ width: 0 }}
          animate={{ width: `${progressPct}%` }}
          transition={{ duration: 0.6, ease: "easeOut" }}
        />
      </div>

      <AnimatePresence mode="wait">
        {allAnswered ? (
          <motion.div
            key="done"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center py-24 space-y-6"
          >
            <p className="font-mono text-[10px] text-accent uppercase tracking-[0.4em]">Session Complete</p>
            <h2 className="font-serif text-5xl">Your report is ready.</h2>
            <p className="text-dim text-sm">
              All {questions.length} questions evaluated.
            </p>
            <button
              onClick={() => router.push(`/report/${session_id}`)}
              className="mt-4 bg-accent text-surface font-mono text-sm font-bold uppercase
                tracking-[0.2em] px-10 py-4 rounded-lg hover:bg-accent/90 accent-glow
                transition-all active:scale-[0.99]"
            >
              View Full Report →
            </button>
          </motion.div>
        ) : currentQ ? (
          <motion.div
            key={currentQ.id}
            initial={{ opacity: 0, x: 24 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -24 }}
            transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
            className="space-y-5"
          >
            {/* Question card */}
            <div className="panel-border bg-panel rounded-2xl p-8 card-shadow">
              {/* Meta row */}
              <div className="flex items-center gap-3 mb-7">
                <span className="font-mono text-[10px] text-dim uppercase tracking-[0.2em]
                  border border-border px-3 py-1 rounded-full">
                  {TYPE_LABELS[currentQ.question_type] || currentQ.question_type}
                </span>
                <span className={`font-mono text-[10px] uppercase tracking-wider ${DIFF_COLORS[currentQ.difficulty] || "text-dim"}`}>
                  {currentQ.difficulty}
                </span>
                <span className="ml-auto font-mono text-[10px] text-muted tnum">
                  Q{current + 1}
                </span>
              </div>

              {/* Question text */}
              <p className="font-serif text-[1.65rem] leading-[1.35] text-text">
                {currentQ.text}
              </p>
            </div>

            {/* Answer area */}
            {!currentState && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.15 }}
                className="space-y-3"
              >
                <textarea
                  value={answer}
                  onChange={(e) => setAnswer(e.target.value)}
                  placeholder="Type your answer here…"
                  rows={7}
                  className="w-full panel-border bg-panel rounded-xl p-5 text-text text-sm
                    placeholder-muted outline-none resize-none font-sans leading-relaxed
                    transition-colors focus:border-accent/30 focus:bg-elevated"
                />
                <button
                  onClick={handleSubmit}
                  disabled={submitting || answer.trim().length < 10}
                  className="w-full bg-accent text-surface font-mono text-sm font-bold uppercase
                    tracking-[0.2em] py-4 rounded-lg hover:bg-accent/90 accent-glow transition-all
                    active:scale-[0.99] disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  {submitting ? "Evaluating…" : "Submit Answer →"}
                </button>
              </motion.div>
            )}

            {/* Evaluation */}
            {currentState && <EvaluationPanel evaluation={currentState.evaluation} />}

            {/* Probe */}
            {currentState?.probe && !currentState.probeAnswered && (
              <ProbeCard
                probe={currentState.probe}
                answer={probeAnswer}
                onChange={setProbeAnswer}
                onSubmit={handleProbeSubmit}
                submitting={submittingProbe}
              />
            )}

            {/* Navigation */}
            {currentState && (currentState.probeAnswered || !currentState.probe) && (
              <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
                {current < questions.length - 1 ? (
                  <button
                    onClick={handleNext}
                    className="w-full panel-border text-dim font-mono text-sm uppercase
                      tracking-[0.2em] py-4 rounded-lg hover:border-muted hover:text-text
                      transition-colors"
                  >
                    Next Question →
                  </button>
                ) : (
                  <button
                    onClick={() => router.push(`/report/${session_id}`)}
                    className="w-full bg-accent text-surface font-mono text-sm font-bold uppercase
                      tracking-[0.2em] py-4 rounded-lg hover:bg-accent/90 accent-glow transition-all"
                  >
                    Finish &amp; View Report →
                  </button>
                )}
              </motion.div>
            )}
          </motion.div>
        ) : null}
      </AnimatePresence>
    </main>
  );
}
