from core import ai_config
from core.config import settings as env
from db.model.ai_settings import AiSettings
from fastapi import APIRouter, Depends
from libs.database.connect import get_db
from schemas.ai_settings import AiSettingsOut, AiSettingsUpdate
from sqlalchemy.orm import Session

router = APIRouter()


def _get_or_create(db: Session) -> AiSettings:
    row = db.get(AiSettings, 1)
    if not row:
        row = AiSettings(id=1)
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def _out(row: AiSettings) -> AiSettingsOut:
    cfg = ai_config.get_ollama()
    return AiSettingsOut(
        ollama_endpoint=row.ollama_endpoint,
        ollama_model=row.ollama_model,
        updated_at=row.updated_at,
        effective_endpoint=cfg.base_url,
        effective_model=cfg.model,
        token_configured=bool(cfg.token),
        graph_configured=bool(env.NEO4J_URI),
    )


@router.get("/", response_model=AiSettingsOut)
def get_ai_settings(db: Session = Depends(get_db)):
    return _out(_get_or_create(db))


@router.put("/", response_model=AiSettingsOut)
def update_ai_settings(data: AiSettingsUpdate, db: Session = Depends(get_db)):
    row = _get_or_create(db)
    for key, value in data.model_dump(exclude_unset=True).items():
        # Chuỗi rỗng = xoá ghi đè, quay về .env
        setattr(row, key, (value or "").strip() or None)
    db.commit()
    db.refresh(row)
    ai_config.invalidate()
    return _out(row)
