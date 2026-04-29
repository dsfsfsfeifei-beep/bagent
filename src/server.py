import logging

from fastapi import (
    Depends,
    FastAPI,
    Header,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
)
from pydantic import BaseModel

from . import sessions
from .agent import build_agent

log = logging.getLogger("bagent")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="bagent")
_agent = build_agent()


# ---- HTTP /chat ---------------------------------------------------------
class ChatIn(BaseModel):
    message: str
    thread_id: str


def require_token(authorization: str = Header(...)) -> str:
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "Authorization must be Bearer <token>")
    return authorization.split(" ", 1)[1].strip()


@app.post("/chat")
async def chat(body: ChatIn, token: str = Depends(require_token)):
    """无 UI 操作能力的纯问答入口。要让 agent 操作页面必须用 WebSocket。"""
    result = await _agent.ainvoke(
        {"messages": [{"role": "user", "content": body.message}]},
        config={"configurable": {"thread_id": body.thread_id, "user_token": token}},
    )
    last = result["messages"][-1]
    return {"reply": getattr(last, "content", str(last))}


@app.get("/healthz")
def healthz():
    return {"ok": True}


# ---- WebSocket /ws/{thread_id} ------------------------------------------
_BEARER_PREFIX = "bearer."


def _extract_token(websocket: WebSocket) -> tuple[str | None, str | None]:
    """从 Sec-WebSocket-Protocol 中抽出 bearer.<token>，返回 (token, accepted_subprotocol)。
    accepted_subprotocol 必须原样回给浏览器，否则连接会被关。
    """
    raw = websocket.headers.get("sec-websocket-protocol", "")
    for proto in (p.strip() for p in raw.split(",")):
        if proto.startswith(_BEARER_PREFIX) and len(proto) > len(_BEARER_PREFIX):
            return proto[len(_BEARER_PREFIX):], proto
    return None, None


@app.websocket("/ws/{thread_id}")
async def ws_endpoint(websocket: WebSocket, thread_id: str):
    token, subprotocol = _extract_token(websocket)
    if not token:
        await websocket.close(code=1008, reason="missing bearer subprotocol")
        return
    await websocket.accept(subprotocol=subprotocol)

    session = await sessions.register(thread_id, websocket, token)
    log.info("ws connected thread_id=%s", thread_id)

    try:
        while True:
            msg = await websocket.receive_json()
            mtype = msg.get("type")

            if mtype == "action_result":
                cmd_id = msg.get("id")
                if cmd_id:
                    session.resolve(cmd_id, msg)

            elif mtype == "user_message":
                text = (msg.get("text") or "").strip()
                if not text:
                    continue
                try:
                    result = await _agent.ainvoke(
                        {"messages": [{"role": "user", "content": text}]},
                        config={
                            "configurable": {
                                "thread_id": thread_id,
                                "user_token": token,
                            }
                        },
                    )
                    reply = getattr(result["messages"][-1], "content", "")
                    await session.send_assistant(reply)
                except Exception as e:
                    log.exception("agent error")
                    await session.send_assistant(f"(出错了：{e})")

            elif mtype == "ping":
                await websocket.send_json({"type": "pong"})

            else:
                log.warning("unknown ws message type: %r", mtype)

    except WebSocketDisconnect:
        log.info("ws disconnected thread_id=%s", thread_id)
    finally:
        sessions.unregister(thread_id, websocket)
