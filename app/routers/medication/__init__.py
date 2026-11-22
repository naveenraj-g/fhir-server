from fastapi import APIRouter

from . import core

router = APIRouter(prefix="/medications", tags=["Medications"])
router.include_router(core.router)
