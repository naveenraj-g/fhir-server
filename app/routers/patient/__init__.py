from fastapi import APIRouter

from . import core

router = APIRouter(prefix="/patients", tags=["Patients"])
router.include_router(core.router)
