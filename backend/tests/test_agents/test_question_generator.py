from unittest.mock import patch

from agents.question_generator import QUESTION_MIX, get_contexts, get_question_plan


def test_get_question_plan_matches_mix():
    plan = get_question_plan()
    assert len(plan) == 8
    assert plan.count("behavioral") == 3
    assert plan.count("technical") == 3
    assert plan.count("situational") == 1
    assert plan.count("resume_deep_dive") == 1
    assert list(QUESTION_MIX.keys()) == ["behavioral", "technical", "situational", "resume_deep_dive"]


def test_get_contexts_joins_retrieved_chunks():
    with patch("agents.question_generator.retrieve_resume_context", return_value=["a", "b"]), \
         patch("agents.question_generator.retrieve_jd_context", return_value=["c"]):
        resume_context, jd_context = get_contexts("session-1", "Backend Engineer")

    assert resume_context == "a\n\nb"
    assert jd_context == "c"
