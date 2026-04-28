from langchain_core.runnables import RunnableConfig


class AuthError(RuntimeError):
    pass


def get_user_token(config: RunnableConfig) -> str:
    token = (config.get("configurable") or {}).get("user_token")
    if not token:
        raise AuthError("user_token missing in RunnableConfig.configurable")
    return token
