from fastapi import APIRouter

from . import core

router = APIRouter(
    prefix="/immunization-recommendations", tags=["ImmunizationRecommendations"]
)
router.include_router(core.router)
