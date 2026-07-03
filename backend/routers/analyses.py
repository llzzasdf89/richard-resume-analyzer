import json

from fastapi import APIRouter, Depends, Form, Request, UploadFile
from fastapi.responses import StreamingResponse

from controllers.analysis_controller import (
    create_analysis_from_upload,
    delete_analysis,
    get_analysis,
    list_analyses,
)
from core.responses import api_error, api_success
from core.security import get_current_user
from services.analysis_stream_service import stream_hub

router = APIRouter(prefix="/analyses")


@router.post("")
async def create_analysis(
    request: Request,
    resume: UploadFile,
    jd_text: str = Form(...),
    job_title: str | None = Form(None),
    company: str | None = Form(None),
    current_user: dict = Depends(get_current_user),
):
    try:
        return await create_analysis_from_upload(
            current_user=current_user,
            request_id=request.state.request_id,
            resume=resume,
            jd_text=jd_text,
            job_title=job_title,
            company=company,
        )
    except ValueError as exc:
        return api_error(str(exc))


@router.get("")
async def get_analyses(current_user: dict = Depends(get_current_user)):
    return api_success({"items": list_analyses(current_user=current_user)})


@router.get("/{analysis_id}")
async def get_analysis_detail(analysis_id: str, current_user: dict = Depends(get_current_user)):
    analysis = get_analysis(current_user=current_user, analysis_id=analysis_id)
    if not analysis:
        return api_error("Analysis not found")
    return api_success(analysis)


@router.delete("/{analysis_id}")
async def delete_analysis_detail(analysis_id: str, current_user: dict = Depends(get_current_user)):
    delete_analysis(current_user=current_user, analysis_id=analysis_id)
    return api_success({"deleted": True})


@router.get("/{analysis_id}/events")
async def analysis_events(
    analysis_id: str,
    current_user: dict = Depends(get_current_user),
):
    analysis = get_analysis(current_user=current_user, analysis_id=analysis_id)
    snapshot_event = _analysis_snapshot_event(analysis) if analysis else {
        "type": "failed",
        "analysis_id": analysis_id,
        "message": "Analysis not found",
    }

    async def generate():
        yield _sse_event(snapshot_event)
        if snapshot_event.get("type") in {"completed", "failed"}:
            return

        async for event in stream_hub.subscribe(analysis_id):
            yield _sse_event(event)

    return StreamingResponse(generate(), media_type="text/event-stream")


def _sse_event(event: dict) -> str:
    return f"event: {event.get('type', 'progress')}\n" f"data: {json.dumps(event)}\n\n"


def _analysis_snapshot_event(analysis: dict) -> dict:
    analysis_id = str(analysis["id"])
    status = analysis["status"]

    if status == "completed":
        return {
            "type": "completed",
            "analysis_id": analysis_id,
            "status": "completed",
            "progress": 100,
            "score": analysis.get("score"),
            "message": "Analysis completed",
            "result": analysis.get("result") or {},
        }

    if status == "failed":
        return {
            "type": "failed",
            "analysis_id": analysis_id,
            "status": "failed",
            "progress": 100,
            "message": analysis.get("error") or "Analysis failed",
        }

    return {
        "type": "progress",
        "analysis_id": analysis_id,
        "step": analysis.get("current_step") or status,
        "status": status,
        "progress": analysis.get("progress") or 0,
        "message": f"Analysis is {status}",
    }
