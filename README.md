# ApplyAI

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

## Deploy Simples Em Producao

Arquitetura recomendada para beta privado e barato:

- Banco: Supabase Postgres com extensao `vector`.
- Backend: Render Web Service usando `backend/Dockerfile`.
- Frontend: Vercel com root directory `frontend`.
- Acesso: senha compartilhada via `APP_ACCESS_TOKEN`.

Observacao de custo: o Render tambem oferece Postgres, mas o banco free expira
apos um periodo curto. Para um beta privado com dados persistentes, Supabase Free
costuma ser o caminho mais barato; se quiser simplificar tudo em um unico
provedor, use Postgres pago no Render.

### 1. Banco

Crie um projeto no Supabase e habilite `pgvector` no SQL editor:

```sql
create extension if not exists vector;
```

Copie a connection string do Postgres para `DATABASE_URL`. A aplicacao aceita tanto
`postgresql://...` quanto `postgresql+psycopg://...`.

### 2. Backend

No Render, use o Blueprint deste repositorio (`render.yaml`) ou crie um Web
Service apontando para este repositorio:

- Root directory: `backend`
- Runtime: Docker
- Dockerfile: `backend/Dockerfile`
- Health check path: `/health`

Variaveis:

```bash
OPENAI_API_KEY=...
DATABASE_URL=...
BACKEND_CORS_ORIGINS=https://SEU-FRONTEND.vercel.app
APP_ACCESS_TOKEN=uma-senha-forte-compartilhada
DEMO_LOGIN_USERNAME=admin
DEMO_LOGIN_PASSWORD=admin
MAX_UPLOAD_BYTES=5000000
DELETE_UPLOADED_PDF_AFTER_PARSE=true
OPENAI_EXTRACTION_MODEL=gpt-4.1-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

O container roda `alembic upgrade head` antes de iniciar a API.

### 3. Frontend

Na Vercel, importe o mesmo repositorio:

- Root directory: `frontend`
- Build command: `npm run build`
- Output: padrao do Next.js

Variavel:

```bash
NEXT_PUBLIC_API_BASE_URL=https://SUA-API.onrender.com
```

Depois de publicar o frontend, volte no backend e ajuste `BACKEND_CORS_ORIGINS`
para a URL final da Vercel.

### 4. Acesso

Compartilhe o link do frontend e a senha definida em `APP_ACCESS_TOKEN`. Sem essa
senha, o frontend mostra a tela de acesso e a API rejeita chamadas privadas.

Para uma demo guiada, configure tambem `DEMO_LOGIN_USERNAME` e
`DEMO_LOGIN_PASSWORD`. Com `admin/admin`, o frontend mostra um login simples de
teste e cria automaticamente um curriculo ficticio e uma vaga demo do Nubank no
primeiro acesso. Use esse login apenas para teste controlado; mantenha
`APP_ACCESS_TOKEN` como um segredo forte no Render.

Roteiro rapido para testers:

1. Acesse a URL da Vercel.
2. Entre com `admin` / `admin`.
3. Selecione a vaga salva do Nubank.
4. Clique em `Run Analysis`.
5. Leia o score, os requisitos e as evidencias encontradas.

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
