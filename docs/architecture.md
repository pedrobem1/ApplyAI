# Architecture

ApplyAI is a web application for comparing job requirements against resume evidence. The product uses LLMs for structured extraction and verification, but keeps retrieval, persistence and scoring inside deterministic application code.

## System Shape

```text
Next.js frontend
  -> FastAPI backend
    -> PostgreSQL + pgvector
    -> OpenAI API
```

## Main Pipeline

```text
Resume PDF
  -> text extraction
  -> structured resume evidence extraction
  -> evidence embeddings
  -> PostgreSQL

Job URL or manual description
  -> scraping and cleaning
  -> structured requirement extraction
  -> requirement embeddings
  -> PostgreSQL

JobRequirement
  -> vector search over ResumeEvidence
  -> LLM verification with retrieved evidence only
  -> RequirementMatch
  -> deterministic backend score
```

## Important Design Decisions

- The LLM does not assign the final compatibility score.
- Requirement matching uses semantic retrieval before LLM verification.
- Structured Outputs and Pydantic schemas are used instead of parsing free-form model text.
- Resume evidence must be grounded in actual resume text.
- Scraping starts generic and simple, with Playwright reserved as a fallback.
- The initial product uses a single user until authentication becomes necessary.
- The agent is a P1 feature layered over structured product data, not a replacement for the pipeline.

## Core Entities

- `User`
- `Resume`
- `ResumeEvidence`
- `Job`
- `JobRequirement`
- `RequirementMatch`
- `UserSkill`
- `AiRun`

## Scoring

Classification points:

```text
MATCH = 1.0
PARTIAL = 0.5
NO_MATCH = 0.0
```

Importance weights:

```text
required = 1.5
preferred = 1.0
nice_to_have = 0.5
unknown = 1.0
```

Formula:

```text
score = weighted_points_obtained / weighted_points_possible
```
