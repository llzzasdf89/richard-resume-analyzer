# Resume Analyzer AI

> An AI-powered resume analysis workspace built with Multi-Agent workflows and RAG.
>
> After signing in, users can upload a PDF resume, paste a target job description, run an asynchronous fit analysis, generate a PDF report, and revisit previous resumes and analysis history.

---

## Breaking Change Notice

The next planned version is a breaking change. It upgrades the project from a single demo-style analysis flow into a product workspace with authentication, history, file storage, and report archiving.

See [CHANGELOG.md](./CHANGELOG.md) for the detailed change log.

---

## Product Positioning

Resume Analyzer AI helps job seekers tailor resumes before applying, especially candidates applying to technical roles.

It focuses on four problems:

- Users do not know how well their resume matches a target job description.
- Users do not know which skill gaps matter most.
- Users do not know how to rewrite resume content for a specific role.
- Users cannot easily find past uploaded resumes and analysis reports.

The new version is centered on a private user workspace. After login, users can upload resumes, analyze job descriptions, view reports, revisit history, and download both the original resume PDF and the generated analysis report PDF.

---

## Scope

### Included In This Iteration

- Google and GitHub OAuth login.
- User-scoped analysis history.
- User-scoped resume file management.
- PDF resume uploads up to `5MB`.
- Original resume PDF storage on the server filesystem.
- Job description analysis.
- Asynchronous AI analysis tasks.
- Real-time progress through SSE.
- Persisted analysis results.
- PDF report generation and download.
- Unified API response shape.
- MVC-style backend restructuring.
- Polished SaaS-style frontend UI.

### Not Included In This Iteration

- Payments, subscriptions, or Pro plans.
- Email/password authentication.
- Team workspaces.
- Object storage services.
- Redis, Celery, RQ, or external task queues.
- Multi-instance backend deployment.
- Public knowledge-base management pages.

---

## Tech Stack

### Frontend

| Area | Technology |
| --- | --- |
| Framework | React + Vite + TypeScript |
| UI | shadcn/ui |
| Styling | Tailwind CSS |
| Icons | lucide-react |
| Auth Client | Supabase JS |
| HTTP | Axios |

### Backend

| Area | Technology |
| --- | --- |
| Web Framework | FastAPI + Uvicorn |
| Concurrency | asyncio |
| AI Orchestration | LangChain + LangGraph |
| RAG | pgvector + PostgreSQL |
| PDF Parsing | PyMuPDF |
| Auth Verification | Supabase JWT |
| File Storage | Local server filesystem + Docker volume |
| Runtime | Python 3.11+ |

### Deployment

| Area | Technology |
| --- | --- |
| Containers | Docker + docker-compose |
| Database | PostgreSQL + pgvector |
| Backend Instance | Single instance |
| Persistent Files | `/app/uploads` Docker volume |

---

## New User Flow

```text
Landing Page
    |
    v
Login with Google/GitHub
    |
    v
Upload Resume PDF
    |
    v
Paste Job Description
    |
    v
POST /api/v1/analyses
    |
    v
Backend starts asyncio analysis task immediately
    |
    v
GET /api/v1/analyses/{analysis_id}/events
    |
    v
Analysis Progress UI
    |
    v
Analysis Result + PDF Report
    |
    v
History / Saved Resumes
```

---

## API Contract

All product APIs use the versioned prefix:

```text
/api/v1
```

### Unified Response Shape

Normal HTTP APIs return HTTP status `200` by default. Business success or failure is determined from the response body.

Success:

```json
{
  "success": true,
  "message": "OK",
  "data": {},
  "code": 200
}
```

Failure:

```json
{
  "success": false,
  "message": "Only PDF files up to 5MB are supported",
  "data": null,
  "code": 500
}
```

### Auth

```http
GET /api/v1/me
```

All `/api/v1/*` product APIs require:

```http
Authorization: Bearer <supabase_access_token>
```

### Analyses

```http
POST   /api/v1/analyses
GET    /api/v1/analyses
GET    /api/v1/analyses/{analysis_id}
GET    /api/v1/analyses/{analysis_id}/events
DELETE /api/v1/analyses/{analysis_id}
```

`POST /api/v1/analyses` uses `multipart/form-data`:

```text
resume: File
jd_text: string
job_title?: string
company?: string
```

After creation, the backend immediately starts an asynchronous analysis task and returns:

```json
{
  "success": true,
  "message": "OK",
  "code": 200,
  "data": {
    "analysis_id": "uuid",
    "resume_id": "uuid",
    "status": "processing"
  }
}
```

`GET /api/v1/analyses/{analysis_id}` returns the current status snapshot or completed result.

`GET /api/v1/analyses/{analysis_id}/events` streams real-time progress with SSE.

### Resumes

```http
GET    /api/v1/resumes
GET    /api/v1/resumes/{resume_id}
GET    /api/v1/resumes/{resume_id}/file
DELETE /api/v1/resumes/{resume_id}
```

Deleting a resume deletes the original PDF file, resume row, associated analyses, associated reports, and generated report PDFs. The frontend must show a destructive confirmation modal.

### Reports

```http
GET    /api/v1/reports
GET    /api/v1/reports/{report_id}
GET    /api/v1/reports/{report_id}/file
DELETE /api/v1/reports/{report_id}
```

The first version generates PDF reports and supports preview/download in the frontend.

### Health

```http
GET /health
```

---

## Data Model

The new version needs these core tables:

- `users`
- `user_identities`
- `resumes`
- `analyses`
- `reports`

`resumes` stores original file metadata and a relative `storage_key`. It does not store file bytes.

`analyses` stores task status, progress, job description text, score, and structured analysis results.

`reports` stores the report content snapshot and generated PDF report file path.

The existing `jd_knowledge` and RAG capability remains an internal backend capability. It is not exposed as a public product API in the first iteration.

---

## Backend Structure

The backend stays flat under `backend/`. Do not add an extra `app/` wrapper directory.

```text
backend/
  main.py
  core/
  middleware/
  routers/
  schemas/
  controllers/
  models/
  services/
  graph/
  eval/
  uploads/
```

Responsibilities:

- `routers`: API routes, dependencies, request declarations, and response declarations.
- `schemas`: Pydantic request and response models.
- `controllers`: Business workflow orchestration.
- `models`: Database access, transactions, and queries.
- `services`: Domain services for auth, file storage, PDF handling, reports, and analysis streaming.
- `middleware`: Request IDs, access logs, and error handling.
- `graph`: LangGraph, RAG, and agent logic.

---

## Observability And Audit Logs

Production logs are part of the product's dispute-resolution and support evidence. They must capture enough request-level context to investigate user complaints without exposing unnecessary secrets.

Backend logging requirements:

- Every request must have a request ID.
- If the frontend retries the same request after a network issue, it must reuse the previous request ID.
- Logs must include the request ID, authenticated user ID, HTTP method, route, important request parameters, response body summary, business `success`, business `code`, latency, and error details when present.
- For analysis requests, logs must include the `analysis_id`, `resume_id`, current state, and progress step.
- For model calls, logs must include the model name, prompt/input summary, response content or response summary, token usage when available, latency, and failure reason when present.
- Logs must be written to files split by day.
- Logs should avoid storing sensitive raw secrets, access tokens, or full binary file content.

Recommended log directory:

```text
/app/logs
```

Docker should mount this directory as a persistent volume in production.

---

## Idempotency And Duplicate Submission Control

Analysis creation must protect users and the backend from duplicate submissions caused by retries, double-clicks, or network instability.

Frontend requirements:

- Every request must include a request ID.
- If a network retry happens, the frontend must reuse the same request ID instead of generating a new one.
- The analysis submit button should remain disabled while the current analysis creation request is pending.

Backend requirements:

- The backend must accept and validate the request ID.
- `POST /api/v1/analyses` must be idempotency-aware.
- The backend should keep an idempotency record keyed by user ID and request ID.
- The backend should maintain an explicit analysis state machine.
- If the same user sends the same request ID again, the backend should return the existing result when safe.
- If the uploaded resume is already associated with an active queued or processing analysis, the backend must reject the new analysis request and return a normal HTTP `200` response with business failure:

```json
{
  "success": false,
  "message": "This resume is already being analyzed. Please wait for the current task to finish.",
  "data": {
    "analysis_id": "uuid",
    "status": "processing"
  },
  "code": 500
}
```

The first version can use a state machine plus a resume task cache. PostgreSQL remains the durable source of truth, while in-memory cache can speed up active-task checks in the single-instance deployment.

Expected analysis states:

```text
queued
processing
completed
failed
deleted
```

Valid state transitions:

```text
queued -> processing
processing -> completed
processing -> failed
completed -> deleted
failed -> deleted
```

Invalid transitions should be rejected and logged with the request ID and user ID.

---

## File Storage

Production uses:

```text
/app/uploads
```

Docker must mount this directory as a persistent volume.

Storage key examples:

```text
resumes/<user_id>/<resume_id>.pdf
reports/<user_id>/<report_id>.pdf
```

Files are not exposed as public static assets. All preview and download requests must go through FastAPI ownership checks.

---

## Development

### Environment

Create a frontend environment file:

```bash
cp frontend/.env.example frontend/.env
```

Then fill in the Supabase project values:

```bash
VITE_API_BASE_URL=http://localhost:8000
VITE_SUPABASE_URL=https://your-project-ref.supabase.co
VITE_SUPABASE_ANON_KEY=your-supabase-anon-key
```

Create a backend environment file:

```bash
cp backend/.env.example backend/.env
```

Then fill in the backend Supabase values:

```bash
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_JWT_SECRET=your-supabase-jwt-secret
```

`SUPABASE_URL` is required for projects that issue `RS256` or `ES256` access tokens, because the backend verifies those tokens through the Supabase JWKS endpoint. `SUPABASE_JWT_SECRET` is still supported for legacy `HS256` tokens.

The Supabase project must enable Google and GitHub OAuth providers, and the local site URL or redirect URL must allow:

```text
http://localhost:5173
http://127.0.0.1:5173
```

### One-Command Startup

```bash
./dev.sh
```

This starts both development servers:

- Backend: `http://127.0.0.1:8000`
- Frontend: `http://127.0.0.1:5173`

The script checks backend and frontend dependencies before startup. If backend dependencies are missing, it runs `uv sync`. If frontend dependencies are missing or stale, it runs `npm install`.

Press `Ctrl+C` in the script terminal to stop both processes.

### Backend

```bash
cd backend
uv sync
uvicorn main:server --reload --host 127.0.0.1 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

### Docker

```bash
docker-compose up -d --build
```

---

## License

MIT
