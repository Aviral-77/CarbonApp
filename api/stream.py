"""Streaming callback handler for real-time agent trace in the UI."""
import json
import asyncio
from datetime import datetime, timezone
from collections.abc import Callable


class StreamingTraceHandler:
    """Captures agent tool calls and results for real-time streaming."""

    def __init__(self, send_event: Callable | None = None):
        self.events: list[dict] = []
        self.send_event = send_event
        self._loop = None

    def _emit(self, event: dict):
        self.events.append(event)
        if self.send_event:
            try:
                if self._loop and self._loop.is_running():
                    self._loop.call_soon_threadsafe(
                        lambda: asyncio.ensure_future(self._async_send(event))
                    )
                else:
                    pass
            except Exception:
                pass

    async def _async_send(self, event: dict):
        if self.send_event:
            await self.send_event(event)

    def set_loop(self, loop):
        self._loop = loop

    def __call__(self, **kwargs):
        event_type = None
        data = {}

        if "current_tool_use" in kwargs:
            tool_use = kwargs["current_tool_use"]
            if isinstance(tool_use, dict):
                event_type = "tool_call"
                data = {
                    "tool": tool_use.get("name", "unknown"),
                    "input": tool_use.get("input", {}),
                }
        elif "current_tool_result" in kwargs:
            tool_result = kwargs["current_tool_result"]
            if isinstance(tool_result, dict):
                event_type = "tool_result"
                data = {
                    "tool": tool_result.get("name", "unknown"),
                    "output": str(tool_result.get("content", ""))[:2000],
                }
        elif "data" in kwargs:
            chunk = kwargs["data"]
            if chunk:
                event_type = "text"
                data = {"text": str(chunk)}

        if event_type:
            self._emit({
                "type": event_type,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                **data,
            })
