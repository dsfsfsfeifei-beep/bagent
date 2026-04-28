from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel

from .agent import build_agent

app = FastAPI(title="bagent")
_agent = build_agent()


class ChatIn(BaseModel):
    message: str
    thread_id: str  # 通常用 user_id 或 user_id+session_id


def require_token(authorization: str = Header(...)) -> str:
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "Authorization must be Bearer <token>")
    return authorization.split(" ", 1)[1].strip()


@app.post("/chat")
def chat(body: ChatIn, token: str = Depends(require_token)):
    result = _agent.invoke(
        {"messages": [{"role": "user", "content": body.message}]},
        config={
            "configurable": {
                "thread_id": body.thread_id,
                "user_token": token,
            }
        },
    )
    last = result["messages"][-1]
    return {"reply": getattr(last, "content", str(last))}


@app.get("/healthz")
def healthz():
    return {"ok": True}
