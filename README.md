# Job Application Intelligence

MVP para analisar vagas em relacao ao curriculo do candidato usando FastAPI, Next.js, PostgreSQL, pgvector e OpenAI.

## Objetivo

Construir uma aplicacao pequena, funcional e tecnicamente defensavel que demonstre:

- parsing de curriculo em PDF;
- importacao de vaga por URL ou descricao manual;
- extracao estruturada de requisitos com LLM;
- evidencias estruturadas do curriculo;
- matching requisito x evidencia usando embeddings e pgvector;
- score deterministico calculado pelo backend;
- dashboard simples para analise individual e agregada.

## Stack

- Backend: Python, FastAPI, SQLAlchemy, Alembic, Pydantic
- Frontend: Next.js, TypeScript
- Banco: PostgreSQL com pgvector
- IA: OpenAI Structured Outputs, embeddings e tool calling
- Scraping: httpx, BeautifulSoup e Playwright como fallback futuro

## Setup Local No Mac

### 1. Ferramentas recomendadas

- VSCode
- Python 3.12+
- Node.js LTS
- Docker Desktop
- GitHub CLI, opcional

### 2. Variaveis de ambiente

```bash
cp .env.example .env
```

Preencha `OPENAI_API_KEY`.

### 3. Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

### 4. Frontend

```bash
cd frontend
npm install
npm run dev
```

### 5. Banco

```bash
docker compose up -d db
```

## Fluxo Vertical Inicial

```text
PDF do curriculo
-> ResumeEvidence
-> embeddings

URL ou texto da vaga
-> JobRequirement
-> embeddings
-> busca vetorial
-> verificacao estruturada
-> score
-> tela de analise
```

## Roadmap De 10 Dias

1. Base do monorepo, banco e API.
2. Upload e parsing de curriculo.
3. Extracao estruturada de evidencias.
4. Cadastro manual de vaga.
5. Scraping simples por URL.
6. Extracao estruturada de requisitos.
7. Embeddings e pgvector.
8. Matching e score.
9. Tela de analise e analytics basico.
10. Logs, metricas de IA, testes, deploy e README final.

