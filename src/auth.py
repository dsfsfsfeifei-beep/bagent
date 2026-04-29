from langchain_core.runnables import RunnableConfig

from . import sessions
from .sessions import Session


class AuthError(RuntimeError):
    pass


def _configurable(config: RunnableConfig) -> dict:
    return config.get("configurable") or {}


def get_user_token(config: RunnableConfig) -> str:
    token = _configurable(config).get("user_token")
    if not token:
        raise AuthError("user_token missing in RunnableConfig.configurable")
    return token


def get_session(config: RunnableConfig) -> Session:
    thread_id = _configurable(config).get("thread_id")
    if not thread_id:
        raise AuthError("thread_id missing in RunnableConfig.configurable")
    s = sessions.get(thread_id)
    if s is None:
        raise AuthError(f"no active UI session for thread_id={thread_id}")
    return s
