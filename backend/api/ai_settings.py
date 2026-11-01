from db.model.ai_settings import AiSettings
from fastapi import APIRouter, Depends
from libs.database.connect import get_db
from schemas.ai_settings import AiSettingsOut, AiSettingsUpdate
from sqlalchemy.orm import Session

router = APIRouter()


def _get_or_create(db: Session) -> AiSettings:
    settings = db.query(AiSettings).filter(AiSettings.id == 1).first()
    if not settings:
        settings = AiSettings(id=1, ollama_model="qwen2.5:14b")
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


@router.get("/", response_model=AiSettingsOut)
def get_ai_settings(db: Session = Depends(get_db)):
    return _get_or_create(db)


@router.put("/", response_model=AiSettingsOut)
def update_ai_settings(data: AiSettingsUpdate, db: Session = Depends(get_db)):
    settings = _get_or_create(db)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(settings, key, value)
    db.commit()
    db.refresh(settings)
    return settings
