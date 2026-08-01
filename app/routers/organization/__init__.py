from fastapi import APIRouter

from . import core

router = APIRouter()
router.include_router(core.router)
