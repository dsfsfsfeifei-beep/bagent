from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    llm_base_url: str
    llm_api_key: str
    llm_model: str

    middle_base_url: str = ""
    ebuy_base_url: str = ""
    srm_base_url: str = ""
    fol_base_url: str = ""

    checkpoint_db: str = "./checkpoints.sqlite"


settings = Settings()
