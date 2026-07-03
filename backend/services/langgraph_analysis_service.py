from collections.abc import AsyncIterator
from typing import Any


NODE_PROGRESS = {
    "jd_analysis": 15,
    "rag_retrieval": 25,
    "match_analysis": 35,
    "supervisor": 50,
    "skill_gap_agent": 62,
    "expression_agent": 68,
    "strategy_agent": 74,
    "aggregate_suggestions": 84,
    "rewrite": 92,
}

NODE_LABELS = {
    "jd_analysis": "Analyzing job description",
    "rag_retrieval": "Retrieving similar job context",
    "match_analysis": "Calculating match score",
    "supervisor": "Selecting specialist agents",
    "skill_gap_agent": "Analyzing skill gaps",
    "expression_agent": "Reviewing resume expression",
    "strategy_agent": "Preparing application strategy",
    "aggregate_suggestions": "Combining recommendations",
    "rewrite": "Optimizing resume content",
}

TRACKED_NODES = set(NODE_LABELS)


async def run_langgraph_analysis(
    *,
    resume_text: str,
    jd_text: str,
    graph_app: Any = None,
) -> AsyncIterator[dict]:
    if graph_app is None:
        from graph import app as graph_app

    result = _empty_result()
    yield _progress_event("parsing", "Resume parsed", 5, status="completed")

    async for event in graph_app.astream_events(
        _initial_state(resume_text=resume_text, jd_text=jd_text),
        version="v2",
    ):
        kind = event["event"]
        node_name = event.get("name", "")

        if node_name not in TRACKED_NODES:
            continue

        if kind == "on_chain_start":
            yield _progress_event(
                node_name,
                NODE_LABELS[node_name],
                NODE_PROGRESS[node_name],
            )
            continue

        if kind != "on_chain_end":
            continue

        output = event["data"].get("output") or {}
        _merge_node_output(result, node_name, output)
        yield {
            "type": "step",
            "step": node_name,
            "status": "completed",
            "progress": NODE_PROGRESS[node_name],
            "message": f"{NODE_LABELS[node_name]} completed",
            "content": output,
        }

    result["current_step"] = "completed"
    yield {
        "type": "completed",
        "status": "completed",
        "progress": 100,
        "score": result["score"],
        "message": "Analysis completed",
        "result": result,
    }


def _initial_state(*, resume_text: str, jd_text: str) -> dict:
    return {
        "messages": [],
        "resume_text": resume_text,
        "jd_text": jd_text,
        "jd_requirements": "",
        "jd_must_skills": [],
        "jd_nice_skills": [],
        "rag_context": "",
        "match_score": 0,
        "matched_skills": [],
        "missing_skills": [],
        "agents_to_run": [],
        "sub_suggestions": [],
        "suggestions": "",
        "rewritten_resume": "",
        "error": "",
    }


def _empty_result() -> dict:
    return {
        "score": 0,
        "current_step": "processing",
        "requirements": "",
        "must_skills": [],
        "nice_skills": [],
        "matched_skills": [],
        "missing_skills": [],
        "rag_context": "",
        "agents_to_run": [],
        "suggestions": "",
        "rewritten_resume": "",
        "steps": [{"step": "parsing", "status": "completed"}],
    }


def _progress_event(step: str, message: str, progress: int, *, status: str = "processing") -> dict:
    return {
        "type": "progress",
        "step": step,
        "status": status,
        "progress": progress,
        "message": message,
    }


def _merge_node_output(result: dict, node_name: str, output: dict) -> None:
    result["steps"].append({"step": node_name, "status": "completed"})

    if node_name == "jd_analysis":
        result["requirements"] = output.get("jd_requirements", "")
        result["must_skills"] = output.get("jd_must_skills", [])
        result["nice_skills"] = output.get("jd_nice_skills", [])
    elif node_name == "rag_retrieval":
        result["rag_context"] = output.get("rag_context", "")
    elif node_name == "match_analysis":
        result["score"] = output.get("match_score", 0)
        result["matched_skills"] = output.get("matched_skills", [])
        result["missing_skills"] = output.get("missing_skills", [])
    elif node_name == "supervisor":
        result["agents_to_run"] = output.get("agents_to_run", [])
    elif node_name in {"skill_gap_agent", "expression_agent", "strategy_agent"}:
        suggestions = output.get("sub_suggestions", [])
        if suggestions:
            existing = result.get("suggestions", "")
            result["suggestions"] = "\n\n---\n\n".join(
                item for item in [existing, *suggestions] if item
            )
    elif node_name == "aggregate_suggestions":
        result["suggestions"] = output.get("suggestions", "")
    elif node_name == "rewrite":
        result["rewritten_resume"] = output.get("rewritten_resume", "")
