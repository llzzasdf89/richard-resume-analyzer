import asyncio

from services.analysis_stream_service import AnalysisStreamHub


def test_subscribe_replays_last_terminal_event_for_late_subscriber():
    async def run():
        hub = AnalysisStreamHub()
        await hub.publish("analysis-1", {"type": "completed", "score": 90})

        events = []
        async for event in hub.subscribe("analysis-1"):
            events.append(event)

        return events

    assert asyncio.run(run()) == [{"type": "completed", "score": 90}]
