from app.schemas.ai import ExtractedJob, ExtractedResume, RequirementVerification
from app.services.ai_client import generate_structured_output


def extract_resume_evidence(raw_resume_text: str) -> ExtractedResume:
    system_prompt = (
        "You extract resume evidence for job matching. Only include evidence grounded in the "
        "resume text. Do not invent skills, employers, projects or achievements."
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
    return result


def extract_job_requirements(clean_job_description: str) -> ExtractedJob:
    system_prompt = (
        "You extract structured job requirements. Keep requirements atomic and preserve the "
        "original wording in raw_text."
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
    return result


def verify_requirement_match(
    *,
    requirement_name: str,
    requirement_raw_text: str,
    evidence: list[dict[str, str | int]],
) -> RequirementVerification:
    system_prompt = (
        "You verify whether retrieved resume evidence satisfies a job requirement. Use only the "
        "provided evidence. If evidence is weak or indirect, classify as PARTIAL. If no evidence "
        "supports the requirement, classify as NO_MATCH."
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
    return result

