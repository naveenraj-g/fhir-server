from fastapi import APIRouter

from . import core

router = APIRouter(prefix="/groups", tags=["Groups"])
router.include_router(core.router)
