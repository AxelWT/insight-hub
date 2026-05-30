from fastapi import APIRouter
from core.config import settings

router = APIRouter(prefix="/api/config", tags=["config"])


@router.get("/models")
def get_models():
    return {"models": settings.available_models}
