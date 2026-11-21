from fastapi import APIRouter

from . import core

router = APIRouter(prefix="/detected-issues", tags=["DetectedIssues"])
router.include_router(core.router)
