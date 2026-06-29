import asyncio

from services.analysis_task_service import ActiveResumeTasks
from services.analysis_task_service import run_analysis_task


def test_active_resume_cache_rejects_duplicate_processing_resume():
    cache = ActiveResumeTasks()

    assert cache.try_start("user-1", "resume-1", "analysis-1") is True
    assert cache.try_start("user-1", "resume-1", "analysis-2") is False
    assert cache.get_active_analysis("user-1", "resume-1") == "analysis-1"


def test_analysis_task_marks_analysis_completed(monkeypatch):
    updates = []
    published = []

    class FakeStreamHub:
        async def publish(self, analysis_id, event):
            published.append((analysis_id, event))

    class FakeConnection:
        def commit(self):
            updates.append(("commit",))

        def rollback(self):
            updates.append(("rollback",))

        def close(self):
            updates.append(("close",))

    monkeypatch.setattr("services.analysis_task_service.stream_hub", FakeStreamHub())
    monkeypatch.setattr("services.analysis_task_service.get_conn", lambda: FakeConnection())

    def fake_mark_started(conn, analysis_id):
        updates.append(("started", analysis_id))

    def fake_mark_completed(conn, analysis_id, result):
        updates.append(("completed", analysis_id, result["score"], result["current_step"]))

    monkeypatch.setattr("services.analysis_task_service.mark_analysis_processing", fake_mark_started)
    monkeypatch.setattr("services.analysis_task_service.mark_analysis_completed", fake_mark_completed)

    asyncio.run(run_analysis_task(user_id="user-1", resume_id="resume-1", analysis_id="analysis-1"))

    assert ("started", "analysis-1") in updates
    assert ("completed", "analysis-1", 87, "completed") in updates
    assert ("commit",) in updates
    assert published[-1][1]["type"] == "completed"
