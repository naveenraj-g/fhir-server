from fastapi import APIRouter

from . import core

router = APIRouter(prefix="/care-plans", tags=["CarePlans"])
router.include_router(core.router)
