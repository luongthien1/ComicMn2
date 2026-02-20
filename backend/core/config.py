from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    media_dir: str = "media"
    app_name: str = "FastAPI Example"


settings = Settings()
