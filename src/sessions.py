"""每个 thread_id 对应一条活跃 WebSocket。
UI tool 通过 Session.call_ui() 把命令推给前端，并 await 前端回执。
单 tab 约束：同一 thread_id 后到的连接踢掉先到的。
"""
import asyncio
from uuid import uuid4

from fastapi import WebSocket


class UIError(RuntimeError):
    pass


class Session:
    def __init__(self, ws: WebSocket, token: str):
        self.ws = ws
        self.token = token
        self._pending: dict[str, asyncio.Future] = {}
        self._send_lock = asyncio.Lock()

    async def call_ui(self, name: str, args: dict, timeout: float = 30.0) -> dict:
        cmd_id = uuid4().hex
        loop = asyncio.get_running_loop()
        fut: asyncio.Future = loop.create_future()
        self._pending[cmd_id] = fut
        try:
            async with self._send_lock:
                await self.ws.send_json(
                    {"type": "action", "id": cmd_id, "name": name, "args": args}
                )
            try:
                payload = await asyncio.wait_for(fut, timeout=timeout)
            except asyncio.TimeoutError as e:
                raise UIError(f"UI action {name} timed out after {timeout}s") from e
            if not payload.get("ok", False):
                raise UIError(payload.get("error") or f"UI action {name} failed")
            return payload.get("data") or {}
        finally:
            self._pending.pop(cmd_id, None)

    def resolve(self, cmd_id: str, payload: dict) -> None:
        fut = self._pending.get(cmd_id)
        if fut and not fut.done():
            fut.set_result(payload)

    async def send_assistant(self, text: str) -> None:
        async with self._send_lock:
            await self.ws.send_json({"type": "assistant_message", "text": text})


_sessions: dict[str, Session] = {}


async def register(thread_id: str, ws: WebSocket, token: str) -> Session:
    old = _sessions.get(thread_id)
    if old is not None:
        try:
            await old.ws.close(code=4000, reason="superseded by new connection")
        except Exception:
            pass
    s = Session(ws, token)
    _sessions[thread_id] = s
    return s


def get(thread_id: str) -> Session | None:
    return _sessions.get(thread_id)


def unregister(thread_id: str, ws: WebSocket) -> None:
    cur = _sessions.get(thread_id)
    if cur is not None and cur.ws is ws:
        _sessions.pop(thread_id, None)
