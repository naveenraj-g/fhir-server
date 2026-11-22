from fastapi import APIRouter

from . import core

router = APIRouter(prefix="/care-teams", tags=["CareTeams"])
router.include_router(core.router)
