from fastapi import APIRouter

from . import core

router = APIRouter(prefix="/activity-definitions", tags=["ActivityDefinitions"])
router.include_router(core.router)
