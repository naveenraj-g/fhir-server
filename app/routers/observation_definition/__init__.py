from fastapi import APIRouter

from . import core

router = APIRouter(prefix="/observation-definitions", tags=["ObservationDefinitions"])
router.include_router(core.router)
