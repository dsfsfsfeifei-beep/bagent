from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM (OpenAI-compatible, e.g. local Ollama)
    llm_base_url: str
    llm_api_key: str
    llm_model: str

    # cloud-longsys-srm 服务根 URL（推供应商/推 FOL/查日志的接口都在这一个服务上）
    srm_base_url: str

    # 默认请求超时（秒）
    http_timeout: float = 15.0

    # 每用户对话记忆持久化
    checkpoint_db: str = "./checkpoints.sqlite"


settings = Settings()
