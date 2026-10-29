from fastapi import APIRouter

from . import core

router = APIRouter(prefix="/appointments", tags=["Appointments"])
router.include_router(core.router)
