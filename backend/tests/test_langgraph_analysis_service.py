import asyncio


class FakeGraph:
    async def astream_events(self, initial_state, version):
        assert version == "v2"
        assert initial_state["resume_text"] == "Python resume"
        assert initial_state["jd_text"] == "Python job"

        yield {"event": "on_chain_start", "name": "jd_analysis", "data": {}}
        yield {
            "event": "on_chain_end",
            "name": "jd_analysis",
            "data": {
                "output": {
                    "jd_requirements": "Build APIs",
                    "jd_must_skills": ["Python"],
                    "jd_nice_skills": ["React"],
                }
            },
        }
        yield {"event": "on_chain_start", "name": "match_analysis", "data": {}}
        yield {
            "event": "on_chain_end",
            "name": "match_analysis",
            "data": {
                "output": {
                    "match_score": 82,
                    "matched_skills": ["Python"],
                    "missing_skills": ["React"],
                }
            },
        }
        yield {"event": "on_chain_start", "name": "rewrite", "data": {}}
        yield {
            "event": "on_chain_end",
            "name": "rewrite",
            "data": {"output": {"rewritten_resume": "Better resume"}},
        }


def collect_events():
    from services.langgraph_analysis_service import run_langgraph_analysis

    async def run():
        return [
            event
            async for event in run_langgraph_analysis(
                resume_text="Python resume",
                jd_text="Python job",
                graph_app=FakeGraph(),
            )
        ]

    return asyncio.run(run())


def test_run_langgraph_analysis_streams_progress_and_final_result():
    events = collect_events()

    assert events[0] == {
        "type": "progress",
        "step": "parsing",
        "status": "completed",
        "progress": 5,
        "message": "Resume parsed",
    }
    assert {
        "type": "progress",
        "step": "match_analysis",
        "status": "processing",
        "progress": 35,
        "message": "Calculating match score",
    } in events

    completed = events[-1]
    assert completed["type"] == "completed"
    assert completed["progress"] == 100
    assert completed["score"] == 82
    assert completed["result"]["requirements"] == "Build APIs"
    assert completed["result"]["matched_skills"] == ["Python"]
    assert completed["result"]["missing_skills"] == ["React"]
    assert completed["result"]["rewritten_resume"] == "Better resume"
    assert completed["result"]["steps"][-1] == {
        "step": "rewrite",
        "status": "completed",
    }
