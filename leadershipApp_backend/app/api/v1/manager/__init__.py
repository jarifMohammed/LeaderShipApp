from fastapi import APIRouter
from app.api.v1.manager.observability import router as observability_router

router = APIRouter()
router.include_router(observability_router)

__all__ = ["router", "observability_router"]

