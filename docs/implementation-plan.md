# Implementation Plan

The goal is a functional MVP in roughly 10 days. Each step should leave the application runnable and easy to explain.

## Phase 1: Foundation

- Monorepo structure.
- FastAPI app with health check.
- Next.js shell.
- PostgreSQL with pgvector through Docker Compose.
- SQLAlchemy models.
- Environment variable configuration.
- Initial README and VSCode setup.

## Phase 2: Resume Pipeline

- Upload resume PDF.
- Extract raw text with `pypdf`.
- Store resume record.
- Use OpenAI Structured Outputs to extract resume evidence.
- Store `ResumeEvidence`.
- Generate embeddings for each evidence unit.

## Phase 3: Job Pipeline

- Add job manually from pasted description.
- Import job by URL with `httpx` and BeautifulSoup.
- Clean page text and remove obvious navigation/footer noise.
- Store raw and clean descriptions.
- Use OpenAI Structured Outputs to extract requirements.
- Store `JobRequirement`.
- Generate embeddings for each requirement.

## Phase 4: Matching

- For each requirement, run vector search against resume evidence.
- Pass only retrieved evidence to the LLM verifier.
- Store `RequirementMatch`.
- Calculate score in backend code.
- Return a complete analysis response to the frontend.

## Phase 5: Product UI

- Resume upload view.
- Job import/manual entry view.
- Job analysis page.
- Requirement table grouped by `MATCH`, `PARTIAL` and `NO_MATCH`.
- Evidence display for every matched requirement.
- Score card.

## Phase 6: Differentiation

- Add manual `UserSkill` records.
- Distinguish `SKILL_GAP` from `EVIDENCE_GAP`.
- Add aggregate analytics.
- Track AI latency, token usage, estimated cost and failures.
- Add a simple tool-calling agent over existing structured data.

## Phase 7: Delivery

- Add focused tests for scoring, extraction validation and matching.
- Improve error handling and logs.
- Prepare deploy configuration.
- Write final technical README.
- Push stable milestones to GitHub.

