import asyncio

from models.analyses import _analysis_row_to_dict
from services.analysis_task_service import run_analysis_task


def test_analysis_task_publishes_graph_events_and_persists_result(monkeypatch):
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

    async def fake_run_langgraph_analysis(*, resume_text, jd_text):
        assert resume_text == "Resume text"
        assert jd_text == "Job text"
        yield {
            "type": "progress",
            "step": "jd_analysis",
            "status": "processing",
            "progress": 15,
            "message": "Analyzing job description",
        }
        yield {
            "type": "completed",
            "status": "completed",
            "progress": 100,
            "score": 91,
            "message": "Analysis completed",
            "result": {
                "score": 91,
                "current_step": "completed",
                "matched_skills": ["Python"],
                "missing_skills": [],
                "steps": [{"step": "jd_analysis", "status": "completed"}],
            },
        }

    def fake_mark_processing(conn, analysis_id):
        updates.append(("processing", analysis_id))

    def fake_mark_completed(conn, analysis_id, result):
        updates.append(("completed", analysis_id, result))

    monkeypatch.setattr("services.analysis_task_service.stream_hub", FakeStreamHub())
    monkeypatch.setattr("services.analysis_task_service.get_conn", lambda: FakeConnection())
    monkeypatch.setattr("services.analysis_task_service.mark_analysis_processing", fake_mark_processing)
    monkeypatch.setattr("services.analysis_task_service.mark_analysis_completed", fake_mark_completed)
    monkeypatch.setattr(
        "services.analysis_task_service.get_analysis_task_payload",
        lambda conn, analysis_id: {
            "id": analysis_id,
            "resume_id": "resume-1",
            "resume_text": "Resume text",
            "jd_text": "Job text",
        },
        raising=False,
    )
    monkeypatch.setattr(
        "services.analysis_task_service.run_langgraph_analysis",
        fake_run_langgraph_analysis,
        raising=False,
    )

    asyncio.run(run_analysis_task(user_id="user-1", resume_id="resume-1", analysis_id="analysis-1"))

    assert ("processing", "analysis-1") in updates
    completed_updates = [update for update in updates if update[0] == "completed"]
    assert completed_updates == [
        (
            "completed",
            "analysis-1",
            {
                "score": 91,
                "current_step": "completed",
                "matched_skills": ["Python"],
                "missing_skills": [],
                "steps": [{"step": "jd_analysis", "status": "completed"}],
            },
        )
    ]
    assert ("commit",) in updates
    assert ("close",) in updates
    assert published[0][1]["type"] == "progress"
    assert published[-1][1]["type"] == "completed"
    assert published[-1][1]["score"] == 91


def test_analysis_row_mapping_includes_persisted_result_fields():
    row = (
        "analysis-1",
        "user-1",
        "resume-1",
        "Job text",
        "Backend Engineer",
        "Acme",
        "completed",
        91,
        100,
        "completed",
        [{"step": "rewrite", "status": "completed"}],
        {"score": 91, "rewritten_resume": "Better resume"},
        None,
        "created",
        "updated",
    )

    mapped = _analysis_row_to_dict(row)

    assert mapped["steps"] == [{"step": "rewrite", "status": "completed"}]
    assert mapped["result"] == {"score": 91, "rewritten_resume": "Better resume"}
    assert mapped["error"] is None
