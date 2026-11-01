from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    POLL_INTERVAL: int = 5
    MAX_CONCURRENT: int = 3
    TASK_TIMEOUT: int = 300
    media_dir: str = "media"
    app_name: str = "ComicMn2"

    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "postgres"
    DB_PASSWORD: str = ""
    DB_NAME: str = "comicmn2"

    GEMINI_API_KEY: str = ""

    # Chat provider: "gemini" hoac "ollama"
    AI_PROVIDER: str = "gemini"

    # Ollama chay tren may khac, dat sau reverse proxy co bearer token
    # (backend/tools/ollama_auth_proxy.py). Ollama khong co xac thuc rieng.
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

    # comic-graphrag-mcp (Neo4j + Ollama GraphRAG) — spawn qua stdio
    MCP_SERVER_PYTHON: str = ""  # đường dẫn python.exe trong venv của comic-graphrag-mcp
    MCP_SERVER_CWD: str = ""     # thư mục gốc project comic-graphrag-mcp


settings = Settings()
