from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    nps_api_key: str
    database_url: str = "postgresql://usnps:usnps@localhost:5432/usnps_tracker"


settings = Settings()
