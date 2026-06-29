# Changelog

## Unreleased

### Breaking Changes

- Redesigns the product from a single demo analysis flow into an authenticated resume analysis workspace.
- Replaces the old `POST /api/analyze` streaming-only contract with versioned REST-style APIs under `/api/v1`.
- Removes public `knowledge` APIs from the product surface. Knowledge/RAG remains an internal backend capability.
- Requires user authentication for product APIs through Supabase Auth.
- Adds persistent user-owned resources for resumes, analyses, and reports.
- Changes normal HTTP API responses to always use HTTP status `200`; business success or failure is determined from the response body.
- Changes analysis execution from request-bound streaming to async background execution with status snapshots and SSE progress events.
- Introduces server-side file persistence for original resume PDFs and generated report PDFs.
- Restructures the backend into a flat MVC-style layout under `backend/`.
- Requires request ID propagation for request tracing, retries, audit logs, and idempotency.
- Adds duplicate analysis submission protection through an analysis state machine and active resume task checks.

### Added

- Supabase Auth integration plan with Google and GitHub login.
- User identity mapping through local `users` and `user_identities` tables.
- User-scoped history for past analyses.
- User-scoped saved resume records.
- Original PDF resume storage on the server filesystem through a Docker volume.
- Generated PDF report storage on the server filesystem.
- `reports` table for persisted analysis report snapshots and downloadable report files.
- `GET /api/v1/me` for current user metadata.
- `POST /api/v1/analyses` to create an analysis and start processing immediately.
- `GET /api/v1/analyses` for paginated analysis history.
- `GET /api/v1/analyses/{analysis_id}` for analysis status snapshots and completed results.
- `GET /api/v1/analyses/{analysis_id}/events` for SSE progress events.
- Resume list, detail, file preview/download, and delete endpoints.
- Report list, detail, file download, and delete endpoints.
- Unified response shape:

```json
{
  "success": true,
  "message": "OK",
  "data": {},
  "code": 200
}
```

- Request ID, access log, and centralized error handling middleware.
- Daily rotating file logs for request/audit logging.
- Request audit logging for request ID, authenticated user, important parameters, response summaries, latency, and business result codes.
- Model-call logging for model name, input summary, response content or summary, token usage when available, latency, and failures.
- Idempotency handling based on user ID and request ID.
- Duplicate active-analysis protection for resumes that are already queued or processing.
- `shadcn/ui` as the single UI component framework, with Tailwind CSS and lucide-react icons.
- Polished SaaS-style UI matching the approved reference direction:
  - dark landing hero
  - Google/GitHub login
  - app shell with sidebar
  - upload resume step
  - paste job description step
  - real-time analysis progress step
  - analysis results step
  - history page
  - saved resumes page

### Changed

- Maximum resume PDF upload size is `5MB`.
- Only PDF resume uploads are supported.
- `POST /api/v1/analyses` accepts `multipart/form-data` with:
  - `resume`
  - `jd_text`
  - optional `job_title`
  - optional `company`
- Backend execution uses FastAPI + `asyncio.create_task(...)` for MVP background analysis.
- Deployment target assumes a single backend instance.
- PostgreSQL remains the durable source of truth for users, resumes, analyses, reports, and progress snapshots.
- Frontend retries must reuse the previous request ID instead of generating a new one.
- `POST /api/v1/analyses` must reject duplicate active analysis attempts for the same resume.
- Analysis status changes must follow the state machine: `queued -> processing -> completed|failed`, with `completed|failed -> deleted`.
- SSE is used only for real-time progress subscriptions; status and result recovery use ordinary JSON APIs.
- Deleting an individual analysis deletes that analysis, its report row, and generated report PDF file.
- Deleting a resume deletes the original PDF file, the resume row, associated analyses, associated reports, and generated report PDF files.

### Removed

- Public `POST /api/knowledge` product endpoint.
- Old direct analysis API contract:

```http
POST /api/analyze
```

- The demo-style frontend flow as the target product experience.
- Payment, Pro, and subscription features from the first iteration scope.
- Email/password authentication from the first iteration scope.
- Redis, Celery, RQ, and external queue infrastructure from the first iteration scope.

### Migration Notes

- Existing frontend API clients must be rewritten to call `/api/v1/analyses` and consume the unified response shape.
- Existing unauthenticated flows must be replaced with Supabase-authenticated requests.
- Existing analysis UI should move from a single upload/result screen to the staged workflow.
- Existing database schema must be expanded with `users`, `user_identities`, `resumes`, `analyses`, and `reports`.
- Existing backend files should be reorganized into the flat MVC-style backend layout:

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
```

- Existing LangGraph/RAG files should move under `backend/graph/` and be called through services/controllers.
- Existing Docker deployment must mount persistent upload storage, for example `/app/uploads`.
