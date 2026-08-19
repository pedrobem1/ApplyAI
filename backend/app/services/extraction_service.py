from typing import Any

from app.schemas.ai import ExtractedJob, ExtractedResume, RequirementVerification
from app.services.ai_client import generate_structured_output


def extract_resume_evidence(raw_resume_text: str) -> ExtractedResume:
    result, _metrics = extract_resume_evidence_with_metrics(raw_resume_text)
    return result


def extract_resume_evidence_with_metrics(
    raw_resume_text: str,
) -> tuple[ExtractedResume, dict[str, Any]]:
    system_prompt = (
        "You extract resume evidence for job matching. Only include evidence grounded in the "
        "resume text. Do not invent skills, employers, projects or achievements. "
        "Use evidence_type only from: experience, project, education, skill, certification."
    )
    user_prompt = f"""
Extract concrete evidence units from this resume. Each evidence item must point to a real
experience, project, education item, skill line or certification in the resume.

Resume:
{raw_resume_text}
"""
    result, _metrics = generate_structured_output(
        schema=ExtractedResume,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )
    return result, _metrics


def extract_job_requirements(clean_job_description: str) -> ExtractedJob:
    result, _metrics = extract_job_requirements_with_metrics(clean_job_description)
    return result


def extract_job_requirements_with_metrics(
    clean_job_description: str,
) -> tuple[ExtractedJob, dict[str, Any]]:
    system_prompt = (
        "You extract structured job requirements. Keep requirements atomic and preserve the "
        "original wording in raw_text. Use category only from: technical, non_technical, "
        "domain, language, education, experience. Use importance only from: required, "
        "preferred, nice_to_have, unknown."
    )
    user_prompt = f"""
Extract the role, company, location and requirements from this job description.
Classify each requirement by category and importance.

Job description:
{clean_job_description}
"""
    result, _metrics = generate_structured_output(
        schema=ExtractedJob,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )
    return result, _metrics


def verify_requirement_match(
    *,
    requirement_name: str,
    requirement_raw_text: str,
    evidence: list[dict[str, str | int]],
) -> RequirementVerification:
    result, _metrics = verify_requirement_match_with_metrics(
        requirement_name=requirement_name,
        requirement_raw_text=requirement_raw_text,
        evidence=evidence,
    )
    return result


def verify_requirement_match_with_metrics(
    *,
    requirement_name: str,
    requirement_raw_text: str,
    evidence: list[dict[str, str | int]],
) -> tuple[RequirementVerification, dict[str, Any]]:
    system_prompt = (
        "You verify whether retrieved resume evidence satisfies a job requirement. Use only the "
        "provided evidence. If evidence is weak or indirect, classify as PARTIAL. If no evidence "
        "supports the requirement, classify as NO_MATCH. Use classification only from: MATCH, "
        "PARTIAL, NO_MATCH. Use gap_type only from: NONE, SKILL_GAP, EVIDENCE_GAP, UNKNOWN."
    )
    user_prompt = f"""
Requirement:
{requirement_name}

Original requirement text:
{requirement_raw_text}

Retrieved resume evidence:
{evidence}
"""
    result, _metrics = generate_structured_output(
        schema=RequirementVerification,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )
    return result, _metrics
