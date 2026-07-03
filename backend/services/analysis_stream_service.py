import asyncio
from collections import defaultdict
from collections.abc import AsyncIterator


class AnalysisStreamHub:
    def __init__(self):
        self._subscribers: dict[str, list[asyncio.Queue[dict]]] = defaultdict(list)
        self._last_events: dict[str, dict] = {}

    async def publish(self, analysis_id: str, event: dict) -> None:
        self._last_events[analysis_id] = event
        for queue in list(self._subscribers.get(analysis_id, [])):
            await queue.put(event)

    async def subscribe(self, analysis_id: str) -> AsyncIterator[dict]:
        queue: asyncio.Queue[dict] = asyncio.Queue()
        self._subscribers[analysis_id].append(queue)
        try:
            if analysis_id in self._last_events:
                event = self._last_events[analysis_id]
                yield event
                if event.get("type") in {"completed", "failed"}:
                    return

            while True:
                event = await queue.get()
                yield event
                if event.get("type") in {"completed", "failed"}:
                    break
        finally:
            if queue in self._subscribers[analysis_id]:
                self._subscribers[analysis_id].remove(queue)


stream_hub = AnalysisStreamHub()
