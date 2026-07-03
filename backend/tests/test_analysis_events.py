from routers.analyses import _analysis_snapshot_event


def test_processing_analysis_snapshot_produces_immediate_progress_event():
    event = _analysis_snapshot_event(
        {
            "id": "analysis-1",
            "status": "processing",
            "progress": 35,
            "current_step": "match_analysis",
            "score": None,
            "result": None,
            "error": None,
        }
    )

    assert event == {
        "type": "progress",
        "analysis_id": "analysis-1",
        "step": "match_analysis",
        "status": "processing",
        "progress": 35,
        "message": "Analysis is processing",
    }


def test_completed_analysis_snapshot_produces_terminal_event():
    event = _analysis_snapshot_event(
        {
            "id": "analysis-1",
            "status": "completed",
            "progress": 100,
            "current_step": "completed",
            "score": 88,
            "result": {"score": 88, "rewritten_resume": "Better resume"},
            "error": None,
        }
    )

    assert event == {
        "type": "completed",
        "analysis_id": "analysis-1",
        "status": "completed",
        "progress": 100,
        "score": 88,
        "message": "Analysis completed",
        "result": {"score": 88, "rewritten_resume": "Better resume"},
    }
