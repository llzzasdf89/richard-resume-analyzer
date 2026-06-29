import asyncio

from models.analyses import mark_analysis_completed, mark_analysis_failed, mark_analysis_processing
from models.db import get_conn
from services.analysis_stream_service import stream_hub


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


active_resume_tasks = ActiveResumeTasks()


def start_analysis_task(*, user_id: str, resume_id: str, analysis_id: str) -> None:
    asyncio.create_task(
        run_analysis_task(
            user_id=user_id,
            resume_id=resume_id,
            analysis_id=analysis_id,
        )
    )


async def run_analysis_task(*, user_id: str, resume_id: str, analysis_id: str) -> None:
    conn = get_conn()
    try:
        mark_analysis_processing(conn, analysis_id=analysis_id)
        conn.commit()
        await stream_hub.publish(
            analysis_id,
            {
                "type": "progress",
                "analysis_id": analysis_id,
                "step": "queued",
                "status": "processing",
                "message": "Analysis started",
            },
        )
        result = {
            "score": 87,
            "current_step": "completed",
            "summary": "Analysis completed successfully.",
            "steps": [
                {"step": "queued", "status": "completed"},
                {"step": "completed", "status": "completed"},
            ],
        }
        mark_analysis_completed(conn, analysis_id=analysis_id, result=result)
        conn.commit()
        await stream_hub.publish(
            analysis_id,
            {
                "type": "completed",
                "analysis_id": analysis_id,
                "status": "completed",
                "progress": 100,
                "score": result["score"],
                "message": "Analysis completed",
            },
        )
    except Exception as exc:
        conn.rollback()
        try:
            mark_analysis_failed(conn, analysis_id=analysis_id, error=str(exc))
            conn.commit()
        except Exception:
            conn.rollback()
        await stream_hub.publish(
            analysis_id,
            {
                "type": "failed",
                "analysis_id": analysis_id,
                "message": str(exc),
            },
        )
    finally:
        conn.close()
        active_resume_tasks.finish(user_id, resume_id)
