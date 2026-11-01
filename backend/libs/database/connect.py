import psycopg
from core.config import settings
from psycopg import Connection
from sqlalchemy import URL, create_engine
from sqlalchemy.orm import sessionmaker

DB_HOST = settings.DB_HOST
DB_PORT = settings.DB_PORT
DB_USER = settings.DB_USER
DB_PASSWORD = settings.DB_PASSWORD
DB_NAME = settings.DB_NAME
# URL.create tự escape mật khẩu (ký tự như ?, @, / làm hỏng URL ghép chuỗi)
DATABASE_URL = URL.create(
    "postgresql+psycopg",
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT,
    database=DB_NAME,
)


def get_connection(
    ssl: bool = False,
    timeout: int = 5,
) -> Connection:
    """
    Tạo và trả về PostgreSQL connection.
    Caller có trách nhiệm đóng connection.
    """
    return psycopg.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        connect_timeout=timeout,
        sslmode="require" if ssl else "disable",
    )


engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionMaker = sessionmaker(bind=engine)


def get_db():
    db = SessionMaker()
    try:
        yield db
    finally:
        db.close()
