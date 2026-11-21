from fastapi import APIRouter

from . import core

router = APIRouter(prefix="/family-member-histories", tags=["FamilyMemberHistories"])
router.include_router(core.router)
