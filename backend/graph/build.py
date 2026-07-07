from langgraph.graph import END, START, StateGraph

from .nodes import evaluator_node, feedback_node, interviewer_node
from .state import InterviewState

_ENTRY_BY_STAGE = {
    "generate_questions": "interviewer",
    "submit_answer": "evaluator",
    "summarize": "feedback",
}


def _route_entry(state: InterviewState) -> str:
    return _ENTRY_BY_STAGE[state["stage"]]


def _route_after_interviewer(state: InterviewState) -> str:
    """More questions left in the plan → loop; otherwise done (covers probe-mode too)."""
    return "interviewer" if state.get("question_plan") else END


def _route_after_evaluator(state: InterviewState) -> str:
    return "interviewer" if state.get("needs_probe") else END


def _build_graph():
    builder = StateGraph(InterviewState)
    builder.add_node("interviewer", interviewer_node)
    builder.add_node("evaluator", evaluator_node)
    builder.add_node("feedback", feedback_node)

    builder.add_conditional_edges(START, _route_entry, ["interviewer", "evaluator", "feedback"])
    builder.add_conditional_edges("interviewer", _route_after_interviewer, ["interviewer", END])
    builder.add_conditional_edges("evaluator", _route_after_evaluator, ["interviewer", END])
    builder.add_edge("feedback", END)

    return builder.compile()


graph = _build_graph()
