from fastapi import APIRouter

from . import core

router = APIRouter(prefix="/procedures", tags=["Procedures"])
router.include_router(core.router)
