from fastapi import APIRouter

from . import core

router = APIRouter(prefix="/specimen-definitions", tags=["SpecimenDefinitions"])
router.include_router(core.router)
