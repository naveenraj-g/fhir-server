from fastapi import APIRouter

from . import core

router = APIRouter(prefix="/episodes-of-care", tags=["EpisodeOfCares"])
router.include_router(core.router)
