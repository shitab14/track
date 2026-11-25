"""In-process real-time broadcaster for meeting events (ADR0009).

Server→client delivery uses Server-Sent Events. This module is the pub/sub
seam: each subscriber (one SSE connection) registers an ``asyncio.Queue`` keyed
by ``meeting_id``; mutating actions publish one event to that meeting's queues.

The meetings row remains the single source of truth (ADR0009 decision 2); this
layer only *notifies*. It is correct for a single Uvicorn worker, which is how
``docker compose up`` runs the stack. Scaling to multiple workers would replace
``publish`` with a shared bus such as Postgres ``LISTEN/NOTIFY``.

Mutating endpoints run in Starlette's threadpool (sync handlers), while the SSE
generators live on the event loop. Delivery therefore crosses threads via
``loop.call_soon_threadsafe``; the loop is captured lazily the first time an SSE
connection subscribes, so no application startup hook is required.
"""
from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any, Dict, Optional, Set


class MeetingBroadcaster:
    def __init__(self) -> None:
        self._subscribers: Dict[str, Set[asyncio.Queue]] = defaultdict(set)
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def bind_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Remember the serving event loop; called by SSE handlers on connect."""
        self._loop = loop

    def subscribe(self, meeting_id: str) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue()
        self._subscribers[meeting_id].add(queue)
        return queue

    def unsubscribe(self, meeting_id: str, queue: asyncio.Queue) -> None:
        subs = self._subscribers.get(meeting_id)
        if not subs:
            return
        subs.discard(queue)
        if not subs:
            self._subscribers.pop(meeting_id, None)

    def has_subscribers(self, meeting_id: str) -> bool:
        return bool(self._subscribers.get(meeting_id))

    def publish(self, meeting_id: str, event: Dict[str, Any]) -> None:
        """Deliver ``event`` to every subscriber of ``meeting_id``.

        Safe to call from a threadpool (sync) handler. When the serving loop is
        known, delivery is scheduled thread-safely onto it; otherwise (e.g. a
        unit test on the loop itself) the queue is fed directly. No subscribers
        means a cheap no-op, so callers may publish unconditionally.
        """
        queues = self._subscribers.get(meeting_id)
        if not queues:
            return
        loop = self._loop
        for queue in list(queues):
            if loop is not None and loop.is_running():
                loop.call_soon_threadsafe(queue.put_nowait, event)
            else:
                queue.put_nowait(event)


# Module-level singleton used across the app process.
broadcaster = MeetingBroadcaster()
