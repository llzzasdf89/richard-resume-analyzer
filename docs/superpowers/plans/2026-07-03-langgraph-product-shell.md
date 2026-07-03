# LangGraph Product Shell Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Keep the new product UI while routing `/api/v1/analyses` through the existing LangGraph resume-analysis workflow.

**Architecture:** The product API remains the entry point for auth, storage, history, and SSE. The async task service loads the persisted resume and analysis, executes a small reusable LangGraph event runner, publishes real workflow events, and stores the final graph-derived result. The React page keeps its current shell but replaces interval progress with authenticated SSE updates.

**Tech Stack:** FastAPI, asyncio, LangGraph `astream_events`, PostgreSQL model helpers, React, TypeScript, Axios, native `fetch` streaming for authenticated SSE.

## Global Constraints

- Keep the new UI and `/api/v1` workspace architecture.
- Do not redesign the UI or remove the old `/api/analyze` demo endpoint.
- Do not call real LLM, embedding, Tavily, or external services from tests.
- Use TDD for backend behavior changes.
- Keep changes scoped to the analysis task, event contract, analysis models, and `NewAnalysisPage`.

---

### Task 1: Add A Testable LangGraph Event Runner

**Files:**
- Create: `backend/services/langgraph_analysis_service.py`
- Test: `backend/tests/test_langgraph_analysis_service.py`

**Interfaces:**
- Consumes: graph-like object with `astream_events(initial_state, version="v2")`.
- Produces: `async def run_langgraph_analysis(*, resume_text: str, jd_text: str, graph_app=None) -> AsyncIterator[dict]`.

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_langgraph_analysis_service.py` with tests that use a fake graph yielding `on_chain_start` and `on_chain_end` events for `jd_analysis`, `match_analysis`, and `rewrite`. Assert emitted events include progress, step completion content, and final completed result with `score`, `matched_skills`, `missing_skills`, and `rewritten_resume`.

- [ ] **Step 2: Run test to verify it fails**

Run: `UV_CACHE_DIR=.uv-cache PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest -p no:debugging tests/test_langgraph_analysis_service.py -v`

Expected: FAIL because `services.langgraph_analysis_service` does not exist.

- [ ] **Step 3: Write minimal implementation**

Create `backend/services/langgraph_analysis_service.py` with node labels, initial state builder, output merge logic, and `run_langgraph_analysis`. The service should import `graph.app` only when `graph_app` is not provided.

- [ ] **Step 4: Run test to verify it passes**

Run: `UV_CACHE_DIR=.uv-cache PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest -p no:debugging tests/test_langgraph_analysis_service.py -v`

Expected: PASS.

### Task 2: Connect The Product Async Task To LangGraph

**Files:**
- Modify: `backend/models/analyses.py`
- Modify: `backend/services/analysis_task_service.py`
- Test: `backend/tests/test_analysis_task_service.py`

**Interfaces:**
- Consumes: `run_langgraph_analysis(resume_text, jd_text)` from Task 1.
- Produces: product SSE events on `stream_hub` and completed `analyses.result_json` records.

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_analysis_task_service.py` with fake DB connection/cursor helpers and monkeypatches for `get_conn`, `run_langgraph_analysis`, and `stream_hub.publish`. Assert `run_analysis_task` reads persisted resume text and JD text, publishes progress events from the runner, calls `mark_analysis_completed` with the graph-derived result, and publishes a final completed event.

- [ ] **Step 2: Run test to verify it fails**

Run: `UV_CACHE_DIR=.uv-cache PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest -p no:debugging tests/test_analysis_task_service.py -v`

Expected: FAIL because the task still writes the mock score result and lacks lookup helpers.

- [ ] **Step 3: Write minimal implementation**

Add model helpers to fetch an analysis payload joined with its resume text. Update `run_analysis_task` to use that payload, publish runner events, persist the final completed event's result, and preserve the existing failed-state behavior.

- [ ] **Step 4: Run test to verify it passes**

Run: `UV_CACHE_DIR=.uv-cache PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest -p no:debugging tests/test_analysis_task_service.py -v`

Expected: PASS.

### Task 3: Expose Persisted Results In Analysis Detail

**Files:**
- Modify: `backend/models/analyses.py`
- Test: extend `backend/tests/test_analysis_task_service.py` or add model-level assertions in a focused test.

**Interfaces:**
- Consumes: `analyses.result_json`, `steps_json`, and `error` columns.
- Produces: `get_analysis_for_user` dictionaries with `steps`, `result`, and `error`.

- [ ] **Step 1: Write the failing test**

Assert `_analysis_row_to_dict` can map rows containing `steps_json`, `result_json`, and `error`, so completed result data is available to product pages.

- [ ] **Step 2: Run test to verify it fails**

Run: `UV_CACHE_DIR=.uv-cache PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest -p no:debugging tests/test_analysis_task_service.py -v`

Expected: FAIL because `_analysis_row_to_dict` currently returns only summary fields.

- [ ] **Step 3: Write minimal implementation**

Update analysis SELECT statements and row mapping to include `steps_json`, `result_json`, and `error` while preserving existing key names.

- [ ] **Step 4: Run test to verify it passes**

Run: `UV_CACHE_DIR=.uv-cache PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest -p no:debugging tests/test_analysis_task_service.py -v`

Expected: PASS.

### Task 4: Subscribe NewAnalysisPage To Real SSE Events

**Files:**
- Modify: `frontend/src/api/analyses.ts`
- Modify: `frontend/src/pages/NewAnalysisPage.tsx`

**Interfaces:**
- Consumes: `createAnalysis` response with `analysis_id`, and `/api/v1/analyses/{analysis_id}/events`.
- Produces: a real-time processing view driven by backend events.

- [ ] **Step 1: Add frontend event types**

Define `AnalysisEvent`, `AnalysisEventType`, and a URL helper in `frontend/src/api/analyses.ts`. Keep `createAnalysis` unchanged except for returning a typed `CreateAnalysisResponse`.

- [ ] **Step 2: Replace interval progress**

In `NewAnalysisPage`, remove `setInterval` progress. After `createAnalysis`, use `fetch(createAnalysisEventsUrl(analysisId), { headers: { Authorization: ... } })` via the existing auth-aware client pattern or Supabase session, parse SSE chunks, and update workflow step status from real event `step` names.

- [ ] **Step 3: Completion behavior**

Move to the results phase only after `type === "completed"`. On `failed`, display the backend message and return to the job phase.

- [ ] **Step 4: Verify TypeScript**

Run: `npm run build`

Expected: PASS.

### Task 5: Final Verification

**Files:**
- No new files.

**Interfaces:**
- Consumes: all prior tasks.
- Produces: verified product workflow integration.

- [ ] **Step 1: Run focused backend tests**

Run: `UV_CACHE_DIR=.uv-cache PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest -p no:debugging tests/test_langgraph_analysis_service.py tests/test_analysis_task_service.py -v`

Expected: PASS.

- [ ] **Step 2: Run existing backend safety tests**

Run: `UV_CACHE_DIR=.uv-cache PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run pytest -p no:debugging tests/test_analysis_state_machine.py tests/test_responses.py tests/test_file_storage_service.py -v`

Expected: PASS.

- [ ] **Step 3: Run frontend build**

Run in `frontend`: `npm run build`

Expected: PASS.
