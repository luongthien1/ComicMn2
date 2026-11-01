from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    media_dir: str = "media"
    app_name: str = "ComicMn2"
    MAX_UPLOAD_MB: int = 10

    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "postgres"
    DB_PASSWORD: str = ""
    DB_NAME: str = "comicmn2"

    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # Chat provider: "gemini" hoac "ollama"
    AI_PROVIDER: str = "gemini"

    # Ollama chay tren may khac, dat sau reverse proxy co bearer token
    # (backend/tools/ollama_auth_proxy.py). Ollama khong co xac thuc rieng.
    # Endpoint/model co the ghi de trong trang Cai dat (xem core/ai_config.py).
    OLLAMA_BASE_URL: str = "http://192.168.1.11:11435"
    OLLAMA_TOKEN: str = ""
    OLLAMA_MODEL: str = "qwen3.5:latest"
    OLLAMA_TIMEOUT: int = 180
    EMBED_MODEL: str = "bge-m3"

    # Neo4j — graph tri thuc truyen (xem research/ de biet kien truc)
    # De trong NEO4J_URI thi chat van chay, chi mat phan tra cuu truyen.
    NEO4J_URI: str = ""
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = ""


settings = Settings()
