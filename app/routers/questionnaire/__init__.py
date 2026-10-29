from fastapi import APIRouter

from . import core

router = APIRouter(prefix="/questionnaires", tags=["Questionnaires"])
router.include_router(core.router)
