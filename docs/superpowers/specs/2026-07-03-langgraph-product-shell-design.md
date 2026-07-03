# LangGraph Product Shell Design

## Goal

Keep the new product UI and `/api/v1` workspace architecture while replacing the current mock analysis task with the existing LangGraph resume-analysis workflow.

## Product Boundary

The new UI remains the user-facing product shell. Login, resume upload, job description input, history, saved resumes, reports, API response shape, authentication, and persisted analysis records continue to use the newer product architecture.

The old workflow remains the analysis engine. After the product API stores and parses the resume PDF, the backend runs the existing LangGraph graph from `backend/graph.py` and streams real node progress back to the new UI.

## Backend Design

`POST /api/v1/analyses` remains the entry point. It continues to validate the PDF, store the original resume, parse text, create a `resumes` row, create an `analyses` row, and start an async task.

`services/analysis_task_service.py` stops writing the hard-coded score result. Instead, it loads the persisted resume text and job description, builds the same initial state used by the old `/api/analyze` endpoint, and runs `analysis_graph.astream_events(..., version="v2")`.

Each tracked LangGraph node publishes a structured event through `stream_hub`:

- `parsing`
- `jd_analysis`
- `rag_retrieval`
- `match_analysis`
- `supervisor`
- `skill_gap_agent`
- `expression_agent`
- `strategy_agent`
- `aggregate_suggestions`
- `rewrite`

When the graph finishes, the task stores a completed result in `analyses.result_json` with score, extracted JD requirements, matched skills, missing skills, suggestions, rewritten resume text, and step metadata. If the graph fails, the existing failed-state path marks the analysis failed and publishes a failed SSE event.

The old `/api/analyze` endpoint can remain as a compatibility/demo route for now, but the product UI must use `/api/v1/analyses`.

## Frontend Design

`NewAnalysisPage` keeps its current visual shell and phase model. The fake interval-based progress is removed.

After `createAnalysis` returns `analysis_id`, the page opens an authenticated SSE connection to `/api/v1/analyses/{analysis_id}/events`. Incoming events update the existing progress panel with real workflow state.

The visible steps become the old engine's real nodes, adapted to the new UI:

- Parsing Resume
- JD Analysis
- RAG Retrieval
- Match Analysis
- Supervisor Routing
- Skill Gap Agent
- Expression Agent
- Strategy Agent
- Aggregate Suggestions
- Resume Rewrite

If a high match score skips supervisor and specialist agents, skipped steps may remain waiting until completion or be marked skipped from the final completed payload. The UI must not block completion on nodes that did not run.

## Event Contract

SSE events use JSON payloads and keep the existing stream hub transport:

```json
{
  "type": "progress",
  "analysis_id": "uuid",
  "step": "match_analysis",
  "status": "processing",
  "progress": 40,
  "message": "Calculating match score"
}
```

Step completion events may include `content` for node-specific output. The final event uses:

```json
{
  "type": "completed",
  "analysis_id": "uuid",
  "status": "completed",
  "progress": 100,
  "score": 82,
  "result": {}
}
```

## Testing

Backend tests should verify that the async analysis task consumes graph events, publishes progress, persists the final graph-derived result, and marks failures correctly. Tests should use a fake graph event source so they do not call external LLM, embedding, Tavily, or database services beyond the existing model layer patterns.

Frontend checks should verify that `NewAnalysisPage` starts an analysis, subscribes to SSE events, maps real node events to visible workflow progress, and moves to results only after a completed event.

## Non-Goals

This change does not redesign the UI, rebuild report generation, add a new queue system, replace LangGraph, add Redis/Celery, or remove the old demo endpoint.
