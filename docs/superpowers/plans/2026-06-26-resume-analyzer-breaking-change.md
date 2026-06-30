# Resume Analyzer Breaking Change Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the authenticated resume analysis workspace described in `README.md` and `CHANGELOG.md`.

**Architecture:** The backend will be reorganized into a flat MVC-style FastAPI app with routers, schemas, controllers, models, services, middleware, and graph modules. The frontend will move from the demo upload/result screen to an authenticated SaaS-style workspace using shadcn/ui, Tailwind, Supabase Auth, versioned APIs, request IDs, and SSE progress.

**Tech Stack:** React + Vite + TypeScript, Tailwind CSS, shadcn/ui, lucide-react, Supabase JS, Axios, FastAPI, asyncio, PostgreSQL + pgvector, PyMuPDF, ReportLab, Supabase JWT verification, Docker volumes.

## Global Constraints

- All README, CHANGELOG, UI text, code comments, logs, and prompts must be English.
- Normal HTTP product APIs return HTTP status `200`; business success/failure is determined by `{ success, message, data, code }`.
- Product APIs use `/api/v1`.
- Auth provider is Supabase Auth with Google and GitHub.
- File upload accepts PDF only, max `5MB`.
- Original resume PDFs and generated report PDFs are stored on the server filesystem, not in the database.
- Production file storage root is `/app/uploads`.
- Production log storage root is `/app/logs`.
- Deployment assumes a single backend instance.
- Backend background execution uses FastAPI + `asyncio.create_task(...)`; no Redis, Celery, RQ, or external queue.
- Frontend retries must reuse the previous request ID.
- Backend must reject duplicate active analysis attempts for a resume already in `queued` or `processing`.
- Logs must include request ID, user, important request parameters, response summary, latency, business result, and model response summaries.
- Use TDD for behavior changes.

---

## File Structure

Backend files to create:

- `backend/core/config.py`: environment settings and constants.
- `backend/core/responses.py`: standard API response helpers.
- `backend/core/security.py`: current-user dependency and Supabase JWT verification.
- `backend/core/logging.py`: daily rotating file logging setup.
- `backend/core/exceptions.py`: application exception classes.
- `backend/middleware/request_id.py`: request ID extraction/generation.
- `backend/middleware/access_log.py`: request/response audit logging.
- `backend/routers/health.py`: health endpoint.
- `backend/routers/auth.py`: `/api/v1/me`.
- `backend/routers/analyses.py`: analysis routes and SSE endpoint.
- `backend/routers/resumes.py`: resume list/detail/file/delete routes.
- `backend/routers/reports.py`: report list/detail/file/delete routes.
- `backend/schemas/common.py`: `ApiResponse`, pagination, common models.
- `backend/schemas/auth.py`: current user response schemas.
- `backend/schemas/analysis.py`: analysis request/response schemas.
- `backend/schemas/resume.py`: resume response schemas.
- `backend/schemas/report.py`: report response schemas.
- `backend/controllers/auth_controller.py`: user sync flow.
- `backend/controllers/analysis_controller.py`: create/list/get/delete analysis orchestration.
- `backend/controllers/resume_controller.py`: resume file read/delete orchestration.
- `backend/controllers/report_controller.py`: report read/delete orchestration.
- `backend/models/users.py`: user table queries.
- `backend/models/identities.py`: identity table queries.
- `backend/models/resumes.py`: resume table queries.
- `backend/models/analyses.py`: analysis table queries and state transitions.
- `backend/models/reports.py`: report table queries.
- `backend/models/idempotency.py`: idempotency record queries.
- `backend/services/file_storage_service.py`: PDF storage and path safety.
- `backend/services/pdf_service.py`: PDF parsing wrapper.
- `backend/services/report_service.py`: PDF report generation.
- `backend/services/analysis_task_service.py`: asyncio task orchestration and active resume cache.
- `backend/services/analysis_stream_service.py`: per-analysis SSE pub/sub.
- `backend/services/model_audit_service.py`: model response logging helper.
- `backend/tests/test_responses.py`: response helper tests.
- `backend/tests/test_file_storage_service.py`: file validation/path tests.
- `backend/tests/test_analysis_state_machine.py`: state transition tests.
- `backend/tests/test_idempotency.py`: duplicate request tests.

Backend files to move/modify:

- `backend/db.py` -> `backend/models/db.py`
- `backend/main.py`: reduce to app setup, middleware, routers, startup.
- `backend/graph.py` -> `backend/graph/graph.py`
- `backend/state.py` -> `backend/graph/state.py`
- `backend/tools.py` -> `backend/graph/tools.py`
- `backend/rag.py` -> `backend/graph/rag.py`
- `backend/pyproject.toml`: add JWT/PDF/test dependencies.
- `backend/dockerfile`: preserve English comments and runtime layout.

Frontend files to create:

- `frontend/src/lib/requestId.ts`: request ID generation and retry reuse support.
- `frontend/src/lib/supabase.ts`: Supabase client.
- `frontend/src/lib/apiClient.ts`: Axios client with auth and request ID.
- `frontend/src/api/analyses.ts`: `/api/v1/analyses` API calls.
- `frontend/src/api/resumes.ts`: resume API calls.
- `frontend/src/api/reports.ts`: report API calls.
- `frontend/src/components/ui/*`: shadcn/ui components.
- `frontend/src/components/layout/AppShell.tsx`: authenticated shell.
- `frontend/src/components/auth/LoginPage.tsx`: Google/GitHub login.
- `frontend/src/components/landing/LandingPage.tsx`: dark hero and How It Works.
- `frontend/src/features/analysis/NewAnalysisPage.tsx`: upload/JD workflow.
- `frontend/src/features/analysis/AnalysisProgressPage.tsx`: SSE progress UI.
- `frontend/src/features/analysis/AnalysisResultPage.tsx`: result/report UI.
- `frontend/src/features/history/HistoryPage.tsx`: analysis history.
- `frontend/src/features/resumes/SavedResumesPage.tsx`: saved resumes and delete confirmation.

Frontend files to modify:

- `frontend/package.json`: add Supabase, lucide, shadcn/Radix helper dependencies.
- `frontend/src/App.tsx`: route between landing/login/workspace states.
- `frontend/src/types/index.ts`: new API/domain types.
- `frontend/src/index.css`: theme tokens and global styles.

Docker/doc files to modify:

- `docker-compose.yml`: add uploads/logs volumes.
- `README.md`: keep current English contract updated if implementation changes exact commands.
- `CHANGELOG.md`: keep Breaking Change entries aligned with implementation.

---

### Task 1: Backend Foundation, Settings, Responses, And Tests

**Files:**
- Create: `backend/core/config.py`
- Create: `backend/core/responses.py`
- Create: `backend/core/exceptions.py`
- Create: `backend/schemas/common.py`
- Create: `backend/tests/test_responses.py`
- Modify: `backend/pyproject.toml`

**Interfaces:**
- Produces: `api_success(data: Any = None, message: str = "OK") -> dict`
- Produces: `api_error(message: str, data: Any = None) -> dict`
- Produces: `Settings` with `api_prefix`, `upload_storage_dir`, `log_dir`, `max_upload_bytes`, `supabase_jwt_secret`

- [ ] **Step 1: Add failing response helper tests**

Create `backend/tests/test_responses.py`:

```python
from core.responses import api_error, api_success


def test_api_success_uses_standard_shape():
    assert api_success({"id": "123"}) == {
        "success": True,
        "message": "OK",
        "data": {"id": "123"},
        "code": 200,
    }


def test_api_error_uses_standard_shape_and_business_code_500():
    assert api_error("Failed") == {
        "success": False,
        "message": "Failed",
        "data": None,
        "code": 500,
    }
```

- [ ] **Step 2: Run tests and verify failure**

Run: `cd backend && uv run pytest tests/test_responses.py -v`

Expected: FAIL because `core.responses` does not exist.

- [ ] **Step 3: Add minimal response helpers and settings**

Create `backend/core/responses.py`:

```python
from typing import Any


def api_success(data: Any = None, message: str = "OK") -> dict[str, Any]:
    return {"success": True, "message": message, "data": data, "code": 200}


def api_error(message: str, data: Any = None) -> dict[str, Any]:
    return {"success": False, "message": message, "data": data, "code": 500}
```

Create `backend/core/config.py`:

```python
from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    api_prefix: str = "/api/v1"
    upload_storage_dir: str = os.getenv("UPLOAD_STORAGE_DIR", "uploads")
    log_dir: str = os.getenv("LOG_DIR", "logs")
    max_upload_bytes: int = int(os.getenv("MAX_UPLOAD_BYTES", str(5 * 1024 * 1024)))
    cors_origins: str = os.getenv("CORS_ORIGINS", "http://localhost:5173")
    supabase_jwt_secret: str = os.getenv("SUPABASE_JWT_SECRET", "")


settings = Settings()
```

Create `backend/core/exceptions.py`:

```python
class AppError(Exception):
    def __init__(self, message: str, data: dict | None = None):
        super().__init__(message)
        self.message = message
        self.data = data
```

Create `backend/schemas/common.py`:

```python
from typing import Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    success: bool
    message: str
    data: T | None
    code: int
```

- [ ] **Step 4: Add pytest dependency**

Modify `backend/pyproject.toml` dependencies:

```toml
"pytest>=9.0.0",
```

- [ ] **Step 5: Run tests**

Run: `cd backend && uv run pytest tests/test_responses.py -v`

Expected: PASS.

---

### Task 2: Backend Database Schema And Models

**Files:**
- Move: `backend/db.py` to `backend/models/db.py`
- Create: `backend/models/users.py`
- Create: `backend/models/identities.py`
- Create: `backend/models/resumes.py`
- Create: `backend/models/analyses.py`
- Create: `backend/models/reports.py`
- Create: `backend/models/idempotency.py`
- Create: `backend/tests/test_analysis_state_machine.py`
- Modify: `backend/main.py`

**Interfaces:**
- Consumes: `settings`
- Produces: `init_db() -> None`
- Produces: `transition_analysis_status(current: str, next_status: str) -> str`
- Produces: CRUD helpers for users, resumes, analyses, reports, and idempotency records.

- [ ] **Step 1: Add failing state machine tests**

Create `backend/tests/test_analysis_state_machine.py`:

```python
import pytest

from models.analyses import transition_analysis_status


def test_allows_queued_to_processing():
    assert transition_analysis_status("queued", "processing") == "processing"


def test_rejects_processing_back_to_queued():
    with pytest.raises(ValueError, match="Invalid analysis state transition"):
        transition_analysis_status("processing", "queued")


def test_allows_completed_to_deleted():
    assert transition_analysis_status("completed", "deleted") == "deleted"
```

- [ ] **Step 2: Run tests and verify failure**

Run: `cd backend && uv run pytest tests/test_analysis_state_machine.py -v`

Expected: FAIL because `models.analyses` does not exist.

- [ ] **Step 3: Create model package and state machine**

Create `backend/models/analyses.py`:

```python
VALID_TRANSITIONS = {
    "queued": {"processing"},
    "processing": {"completed", "failed"},
    "completed": {"deleted"},
    "failed": {"deleted"},
    "deleted": set(),
}


def transition_analysis_status(current: str, next_status: str) -> str:
    if next_status not in VALID_TRANSITIONS.get(current, set()):
        raise ValueError(f"Invalid analysis state transition: {current} -> {next_status}")
    return next_status
```

- [ ] **Step 4: Move database initialization into models**

Move `backend/db.py` to `backend/models/db.py` and expand `init_db()` to create:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE TABLE IF NOT EXISTS users (...);
CREATE TABLE IF NOT EXISTS user_identities (...);
CREATE TABLE IF NOT EXISTS resumes (...);
CREATE TABLE IF NOT EXISTS analyses (...);
CREATE TABLE IF NOT EXISTS reports (...);
CREATE TABLE IF NOT EXISTS idempotency_keys (...);
CREATE TABLE IF NOT EXISTS jd_knowledge (...);
```

The table columns must match `README.md`.

- [ ] **Step 5: Add repository helpers**

Add focused functions:

```python
def create_resume(conn, *, user_id: str, original_filename: str, storage_key: str, file_size: int, mime_type: str, parsed_text: str) -> dict: ...
def create_analysis(conn, *, user_id: str, resume_id: str, jd_text: str, job_title: str | None, company: str | None) -> dict: ...
def find_active_analysis_for_resume(conn, *, user_id: str, resume_id: str) -> dict | None: ...
def create_report(conn, *, user_id: str, analysis_id: str, title: str, content: str, storage_key: str) -> dict: ...
```

- [ ] **Step 6: Run tests**

Run: `cd backend && uv run pytest tests/test_analysis_state_machine.py -v`

Expected: PASS.

---

### Task 3: Request ID, Logging, And Audit Middleware

**Files:**
- Create: `backend/core/logging.py`
- Create: `backend/middleware/request_id.py`
- Create: `backend/middleware/access_log.py`
- Create: `backend/tests/test_request_id.py`
- Modify: `backend/main.py`

**Interfaces:**
- Produces: `get_request_id(request: Request) -> str`
- Produces: `RequestIdMiddleware`
- Produces: daily rotating logs under `settings.log_dir`

- [ ] **Step 1: Add failing request ID tests**

Create `backend/tests/test_request_id.py`:

```python
from starlette.requests import Request

from middleware.request_id import REQUEST_ID_HEADER, resolve_request_id


def test_uses_existing_request_id_from_header():
    scope = {"type": "http", "headers": [(REQUEST_ID_HEADER.lower().encode(), b"req_123")]}
    request = Request(scope)
    assert resolve_request_id(request) == "req_123"


def test_generates_request_id_when_missing():
    scope = {"type": "http", "headers": []}
    request = Request(scope)
    assert resolve_request_id(request).startswith("req_")
```

- [ ] **Step 2: Run tests and verify failure**

Run: `cd backend && uv run pytest tests/test_request_id.py -v`

Expected: FAIL because middleware does not exist.

- [ ] **Step 3: Implement request ID middleware**

Create `backend/middleware/request_id.py`:

```python
from uuid import uuid4
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

REQUEST_ID_HEADER = "X-Request-ID"


def resolve_request_id(request: Request) -> str:
    existing = request.headers.get(REQUEST_ID_HEADER)
    return existing if existing else f"req_{uuid4().hex}"


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = resolve_request_id(request)
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request_id
        return response
```

- [ ] **Step 4: Implement daily file logging**

Create `backend/core/logging.py` with `TimedRotatingFileHandler(when="midnight", backupCount=30)`.

- [ ] **Step 5: Implement access log middleware**

Create `backend/middleware/access_log.py` to log method, route, request ID, user ID when present, latency, and response status. For response bodies, log a summary only.

- [ ] **Step 6: Register middleware in main**

Modify `backend/main.py` to register `RequestIdMiddleware` before `AccessLogMiddleware`.

- [ ] **Step 7: Run tests**

Run: `cd backend && uv run pytest tests/test_request_id.py -v`

Expected: PASS.

---

### Task 4: Auth And Current User Sync

**Files:**
- Create: `backend/core/security.py`
- Create: `backend/schemas/auth.py`
- Create: `backend/controllers/auth_controller.py`
- Create: `backend/routers/auth.py`
- Create: `backend/tests/test_auth_controller.py`
- Modify: `backend/pyproject.toml`

**Interfaces:**
- Produces: `get_current_user(request: Request) -> dict`
- Produces: `sync_user_from_claims(conn, claims: dict) -> dict`
- Produces: `GET /api/v1/me`

- [ ] **Step 1: Add failing user sync test**

Create `backend/tests/test_auth_controller.py` with a fake repository call around:

```python
from controllers.auth_controller import normalize_user_claims


def test_normalize_user_claims_from_supabase_jwt():
    claims = {
        "sub": "user-123",
        "email": "dev@example.com",
        "user_metadata": {"name": "Dev User", "avatar_url": "https://example.com/a.png"},
        "app_metadata": {"provider": "github"},
    }
    assert normalize_user_claims(claims) == {
        "provider": "supabase",
        "provider_user_id": "user-123",
        "auth_provider": "github",
        "email": "dev@example.com",
        "name": "Dev User",
        "avatar_url": "https://example.com/a.png",
    }
```

- [ ] **Step 2: Run tests and verify failure**

Run: `cd backend && uv run pytest tests/test_auth_controller.py -v`

Expected: FAIL because controller does not exist.

- [ ] **Step 3: Add JWT dependency**

Modify `backend/pyproject.toml`:

```toml
"pyjwt[crypto]>=2.10.0",
```

- [ ] **Step 4: Implement claim normalization and current user dependency**

Create `backend/controllers/auth_controller.py` and `backend/core/security.py`.

`security.py` must read `Authorization: Bearer <token>`, decode Supabase JWT, sync the local user, and attach `request.state.user`.

- [ ] **Step 5: Add `/api/v1/me` router**

Create `backend/routers/auth.py` returning:

```python
return api_success(current_user)
```

- [ ] **Step 6: Run tests**

Run: `cd backend && uv run pytest tests/test_auth_controller.py -v`

Expected: PASS.

---

### Task 5: File Storage, PDF Parsing, And Report Generation

**Files:**
- Create: `backend/services/file_storage_service.py`
- Create: `backend/services/pdf_service.py`
- Create: `backend/services/report_service.py`
- Create: `backend/tests/test_file_storage_service.py`
- Modify: `backend/pyproject.toml`
- Modify: `docker-compose.yml`

**Interfaces:**
- Produces: `validate_pdf_upload(filename: str, content_type: str, size: int) -> None`
- Produces: `store_resume_pdf(user_id: str, resume_id: str, file_bytes: bytes) -> str`
- Produces: `generate_report_pdf(user_id: str, report_id: str, content: str) -> str`

- [ ] **Step 1: Add failing file validation tests**

Create `backend/tests/test_file_storage_service.py`:

```python
import pytest

from services.file_storage_service import validate_pdf_upload


def test_accepts_pdf_under_5mb():
    validate_pdf_upload("resume.pdf", "application/pdf", 1024)


def test_rejects_non_pdf_extension():
    with pytest.raises(ValueError, match="Only PDF files up to 5MB are supported"):
        validate_pdf_upload("resume.txt", "text/plain", 1024)


def test_rejects_pdf_over_5mb():
    with pytest.raises(ValueError, match="Only PDF files up to 5MB are supported"):
        validate_pdf_upload("resume.pdf", "application/pdf", 5 * 1024 * 1024 + 1)
```

- [ ] **Step 2: Run tests and verify failure**

Run: `cd backend && uv run pytest tests/test_file_storage_service.py -v`

Expected: FAIL because service does not exist.

- [ ] **Step 3: Implement file storage service**

Create `backend/services/file_storage_service.py` with validation, safe storage key generation, and path traversal protection.

- [ ] **Step 4: Implement PDF and report services**

Move PDF parsing into `backend/services/pdf_service.py`.

Add `reportlab>=4.2.0` to `backend/pyproject.toml`.

Create `backend/services/report_service.py` that writes a simple professional PDF report for MVP.

- [ ] **Step 5: Update Docker volumes**

Modify `docker-compose.yml`:

```yaml
volumes:
  - uploads:/app/uploads
  - logs:/app/logs
```

Add named volumes:

```yaml
uploads:
logs:
```

- [ ] **Step 6: Run tests**

Run: `cd backend && uv run pytest tests/test_file_storage_service.py -v`

Expected: PASS.

---

### Task 6: Async Analysis Task Service, Idempotency, And SSE

**Files:**
- Create: `backend/services/analysis_stream_service.py`
- Create: `backend/services/analysis_task_service.py`
- Create: `backend/tests/test_idempotency.py`
- Modify: `backend/graph/*`

**Interfaces:**
- Produces: `AnalysisStreamHub.publish(analysis_id: str, event: dict) -> None`
- Produces: `AnalysisStreamHub.subscribe(analysis_id: str) -> AsyncIterator[dict]`
- Produces: `start_analysis_task(analysis_id: str) -> None`
- Produces: active resume cache keyed by `(user_id, resume_id)`

- [ ] **Step 1: Add failing duplicate active analysis test**

Create `backend/tests/test_idempotency.py`:

```python
from services.analysis_task_service import ActiveResumeTasks


def test_active_resume_cache_rejects_duplicate_processing_resume():
    cache = ActiveResumeTasks()
    assert cache.try_start("user-1", "resume-1", "analysis-1") is True
    assert cache.try_start("user-1", "resume-1", "analysis-2") is False
    assert cache.get_active_analysis("user-1", "resume-1") == "analysis-1"
```

- [ ] **Step 2: Run tests and verify failure**

Run: `cd backend && uv run pytest tests/test_idempotency.py -v`

Expected: FAIL because service does not exist.

- [ ] **Step 3: Implement active resume cache**

Create `backend/services/analysis_task_service.py`:

```python
class ActiveResumeTasks:
    def __init__(self):
        self._active: dict[tuple[str, str], str] = {}

    def try_start(self, user_id: str, resume_id: str, analysis_id: str) -> bool:
        key = (user_id, resume_id)
        if key in self._active:
            return False
        self._active[key] = analysis_id
        return True

    def finish(self, user_id: str, resume_id: str) -> None:
        self._active.pop((user_id, resume_id), None)

    def get_active_analysis(self, user_id: str, resume_id: str) -> str | None:
        return self._active.get((user_id, resume_id))
```

- [ ] **Step 4: Implement stream hub**

Create `backend/services/analysis_stream_service.py` with per-analysis `asyncio.Queue` subscribers and JSON SSE formatting.

- [ ] **Step 5: Implement async graph runner**

`start_analysis_task` must:

1. Transition analysis to `processing`.
2. Parse PDF text if needed.
3. Run LangGraph.
4. Publish progress events.
5. Persist progress snapshots.
6. Generate report PDF.
7. Transition to `completed` or `failed`.
8. Clear the active resume cache in `finally`.

- [ ] **Step 6: Run tests**

Run: `cd backend && uv run pytest tests/test_idempotency.py -v`

Expected: PASS.

---

### Task 7: REST Routers And Controllers

**Files:**
- Create: `backend/routers/health.py`
- Create: `backend/routers/analyses.py`
- Create: `backend/routers/resumes.py`
- Create: `backend/routers/reports.py`
- Create: `backend/controllers/analysis_controller.py`
- Create: `backend/controllers/resume_controller.py`
- Create: `backend/controllers/report_controller.py`
- Modify: `backend/main.py`

**Interfaces:**
- Produces: all routes listed in `README.md`

- [ ] **Step 1: Add API tests for response shape**

Create `backend/tests/test_api_contract.py`:

```python
from fastapi.testclient import TestClient
from main import server


def test_health_returns_ok():
    client = TestClient(server)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
```

- [ ] **Step 2: Run tests and verify baseline**

Run: `cd backend && uv run pytest tests/test_api_contract.py -v`

Expected: PASS for `/health`; protected routes can be added after auth test helpers exist.

- [ ] **Step 3: Implement routers**

`POST /api/v1/analyses` must:

1. Require current user.
2. Require request ID.
3. Validate file.
4. Create or reuse idempotency record.
5. Check duplicate active resume.
6. Create records.
7. Start background task.
8. Return standard response.

- [ ] **Step 4: Register routers in main**

`backend/main.py` should only configure app, middleware, CORS, lifespan, and routers.

- [ ] **Step 5: Run backend tests**

Run: `cd backend && uv run pytest tests -v`

Expected: PASS.

---

### Task 8: Frontend Dependencies, API Client, Auth, And Request IDs

**Files:**
- Modify: `frontend/package.json`
- Create: `frontend/src/lib/requestId.ts`
- Create: `frontend/src/lib/supabase.ts`
- Create: `frontend/src/lib/apiClient.ts`
- Create: `frontend/src/api/analyses.ts`
- Create: `frontend/src/api/resumes.ts`
- Create: `frontend/src/api/reports.ts`
- Modify: `frontend/src/types/index.ts`

**Interfaces:**
- Produces: `createRequestId() -> string`
- Produces: `apiClient`
- Produces: `createAnalysis(input: CreateAnalysisInput, requestId: string)`

- [ ] **Step 1: Add dependencies**

Run:

```bash
cd frontend
npm install @supabase/supabase-js lucide-react clsx tailwind-merge class-variance-authority @radix-ui/react-slot @radix-ui/react-dialog @radix-ui/react-tabs @radix-ui/react-tooltip @radix-ui/react-progress
```

- [ ] **Step 2: Add request ID helper**

Create `frontend/src/lib/requestId.ts`:

```ts
export function createRequestId() {
  return `req_${crypto.randomUUID().replaceAll("-", "")}`
}
```

- [ ] **Step 3: Add Supabase and Axios clients**

`apiClient` must attach:

- `Authorization: Bearer <token>` when logged in.
- `X-Request-ID` from the caller.
- Response interceptor that throws when `success === false` or `code !== 200`.

- [ ] **Step 4: Add typed API wrappers**

Create `analyses.ts`, `resumes.ts`, and `reports.ts` around `/api/v1`.

- [ ] **Step 5: Run build**

Run: `cd frontend && npm run build`

Expected: PASS.

---

### Task 9: Frontend Product UI And Workflow

**Files:**
- Create: `frontend/src/components/ui/*`
- Create: `frontend/src/components/layout/AppShell.tsx`
- Create: `frontend/src/components/auth/LoginPage.tsx`
- Create: `frontend/src/components/landing/LandingPage.tsx`
- Create: `frontend/src/features/analysis/NewAnalysisPage.tsx`
- Create: `frontend/src/features/analysis/AnalysisProgressPage.tsx`
- Create: `frontend/src/features/analysis/AnalysisResultPage.tsx`
- Create: `frontend/src/features/history/HistoryPage.tsx`
- Create: `frontend/src/features/resumes/SavedResumesPage.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/index.css`

**Interfaces:**
- Consumes: API wrappers from Task 8.
- Produces: usable MVP UI matching the approved reference direction.

- [ ] **Step 1: Add shadcn-compatible primitives**

Implement Button, Card, Badge, Tabs, Dialog, Progress, Textarea, Input, Tooltip, and Skeleton components using the installed Radix packages and Tailwind.

- [ ] **Step 2: Build landing and login screens**

Landing must use dark hero, product preview, and How It Works cards.

Login must show Google and GitHub buttons and no email/password form.

- [ ] **Step 3: Build authenticated app shell**

Sidebar items:

- New Analysis
- History
- Saved Resumes

No payment/Pro UI.

- [ ] **Step 4: Build new analysis workflow**

Step 1 uploads PDF.

Step 2 pastes job description.

Step 3 creates analysis with a stable request ID and connects to SSE.

Step 4 shows result and report download.

- [ ] **Step 5: Build history and saved resumes**

History lists analyses.

Saved Resumes lists resumes and uses destructive confirmation before delete.

- [ ] **Step 6: Run frontend checks**

Run: `cd frontend && npm run build`

Expected: PASS.

---

### Task 10: Docker, Documentation Alignment, And Final Verification

**Files:**
- Modify: `docker-compose.yml`
- Modify: `README.md`
- Modify: `CHANGELOG.md`
- Verify: all touched files

**Interfaces:**
- Produces: runnable Docker deployment with database, uploads, and logs volumes.

- [ ] **Step 1: Update Docker volumes**

Ensure backend service includes:

```yaml
volumes:
  - uploads:/app/uploads
  - logs:/app/logs
```

Ensure root volumes include:

```yaml
uploads:
logs:
```

- [ ] **Step 2: Run language scan**

Run:

```bash
rg -n "[\\p{Han}]" README.md CHANGELOG.md frontend/src backend || true
```

Expected: no output.

- [ ] **Step 3: Run backend checks**

Run:

```bash
cd backend
uv run pytest tests -v
python -m py_compile db.py main.py graph.py rag.py state.py tools.py eval/fixtures.py eval/run_eval.py
```

Expected: PASS.

- [ ] **Step 4: Run frontend checks**

Run:

```bash
cd frontend
npm run build
```

Expected: PASS.

- [ ] **Step 5: Run Docker build**

Run:

```bash
docker-compose build
```

Expected: backend and frontend images build successfully.

---

## Self-Review

- Spec coverage: UI, Supabase Auth, local files, PDF reports, REST APIs, HTTP-200 response contract, SSE, asyncio background tasks, logs, request IDs, idempotency, state machine, deletion policy, Docker volumes, and English-only rule are covered.
- Placeholder scan: no TBD/TODO placeholders are used as implementation instructions.
- Type consistency: `analysis_id`, `resume_id`, request ID, `ApiResponse`, and analysis states are consistently named across tasks.

