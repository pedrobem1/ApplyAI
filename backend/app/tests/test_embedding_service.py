from types import SimpleNamespace

from app.services.embedding_service import _job_requirement_text, _resume_evidence_text


def test_resume_evidence_text_includes_skill_evidence_and_source() -> None:
    item = SimpleNamespace(
        skill="Python",
        evidence_text="Built APIs with Python.",
        source="Project A",
    )

    assert _resume_evidence_text(item) == (
        "Skill: Python\nEvidence: Built APIs with Python.\nSource: Project A"
    )


def test_job_requirement_text_includes_matching_context() -> None:
    item = SimpleNamespace(
        name="Docker",
        category="technical",
        importance="preferred",
        raw_text="Docker is preferred.",
    )

    assert _job_requirement_text(item) == (
        "Requirement: Docker\n"
        "Category: technical\n"
        "Importance: preferred\n"
        "Original text: Docker is preferred."
    )
