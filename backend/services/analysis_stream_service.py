import asyncio
from collections import defaultdict
from collections.abc import AsyncIterator


class AnalysisStreamHub:
    def __init__(self):
        self._subscribers: dict[str, list[asyncio.Queue[dict]]] = defaultdict(list)

    async def publish(self, analysis_id: str, event: dict) -> None:
        for queue in list(self._subscribers.get(analysis_id, [])):
            await queue.put(event)

    async def subscribe(self, analysis_id: str) -> AsyncIterator[dict]:
        queue: asyncio.Queue[dict] = asyncio.Queue()
        self._subscribers[analysis_id].append(queue)
        try:
            while True:
                event = await queue.get()
                yield event
                if event.get("type") in {"completed", "failed"}:
                    break
        finally:
            self._subscribers[analysis_id].remove(queue)


stream_hub = AnalysisStreamHub()
