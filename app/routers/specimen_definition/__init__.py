from fastapi import APIRouter

from app.routers.specimen_definition.core import router as core_router

router = APIRouter(prefix="/specimen-definitions", tags=["SpecimenDefinitions"])
router.include_router(core_router)

__all__ = ["router"]
