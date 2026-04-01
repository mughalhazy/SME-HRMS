from services.recruitment import (
    InterviewWorkflow,
    generate_onboarding_checklist,
    parse_cv,
    rank_candidates,
    score_candidate,
)


def test_parse_cv_from_text_extracts_required_fields() -> None:
    cv_text = """Name: Ada Lovelace
Skills:
Python, SQL, Leadership
Experience:
5 years - Backend Engineer
2 years - Team Lead
Education:
BSc Computer Science
"""

    profile = parse_cv(cv_text)

    assert profile.name == "Ada Lovelace"
    assert profile.skills == ["Python", "SQL", "Leadership"]
    assert profile.experience == ["5 years - Backend Engineer", "2 years - Team Lead"]
    assert profile.education == ["BSc Computer Science"]


def test_parse_cv_from_pdf_like_bytes_extracts_sections() -> None:
    pdf_like = b"""%PDF-1.4\n1 0 obj\n<< /Length 120 >>\nstream
BT
(Ada Lovelace) Tj
(Skills:) Tj
(Python, SQL, Leadership) Tj
(Experience:) Tj
(6 years - Software Engineer) Tj
(Education:) Tj
(MSc Data Science) Tj
ET
endstream
endobj
"""

    profile = parse_cv(pdf_like)

    assert profile.name == "Ada Lovelace"
    assert "Python" in profile.skills
    assert profile.experience == ["6 years - Software Engineer"]
    assert profile.education == ["MSc Data Science"]


def test_candidate_scoring_is_deterministic_and_explainable() -> None:
    profile = parse_cv(
        """Name: Ada Lovelace
Skills:
Python, SQL
Experience:
6 years - Backend
Education:
BSc Computer Science
"""
    )

    score_a = score_candidate(profile, ["Python", "SQL", "Leadership"], 5)
    score_b = score_candidate(profile, ["Python", "SQL", "Leadership"], 5)

    assert score_a.score == score_b.score
    assert score_a.explanation == score_b.explanation
    assert "weighted_score=0.7*skills+0.3*experience" in score_a.explanation
    assert score_a.score == 76.67


def test_candidate_ranking_sorts_by_score_descending() -> None:
    alpha = score_candidate(parse_cv("Name: Alpha\nSkills:\nPython\nExperience:\n8 years\nEducation:\nBSc"), ["Python"], 5)
    beta = score_candidate(parse_cv("Name: Beta\nSkills:\nPython\nExperience:\n2 years\nEducation:\nBSc"), ["Python"], 5)
    gamma = score_candidate(parse_cv("Name: Gamma\nSkills:\nGo\nExperience:\n9 years\nEducation:\nBSc"), ["Python"], 5)

    ranked = rank_candidates([beta, gamma, alpha])

    assert [candidate.candidate_name for candidate in ranked] == ["Alpha", "Beta", "Gamma"]


def test_interview_workflow_progression_is_controlled() -> None:
    workflow = InterviewWorkflow(stages=["Applied", "Screening", "Interview", "Offer", "Hired"])

    workflow.define_candidate("cand-1")
    assert workflow.current_stage("cand-1") == "Applied"

    workflow.move_candidate("cand-1", "Screening")
    workflow.move_candidate("cand-1", "Interview")

    assert workflow.current_stage("cand-1") == "Interview"


def test_interview_workflow_rejects_backward_move() -> None:
    workflow = InterviewWorkflow(stages=["Applied", "Screening", "Interview"])
    workflow.define_candidate("cand-2", "Screening")

    try:
        workflow.move_candidate("cand-2", "Applied")
        assert False, "Expected ValueError for backward move"
    except ValueError as exc:
        assert "backwards" in str(exc)


def test_onboarding_checklist_generation_and_assignment() -> None:
    checklist = generate_onboarding_checklist("Ada Lovelace", ["HR", "IT"])

    assert len(checklist) == 5
    assert checklist[0].stage == "Preboarding"
    assert checklist[0].assignee == "HR"
    assert checklist[1].assignee == "IT"
    assert "Ada Lovelace" in checklist[0].task
