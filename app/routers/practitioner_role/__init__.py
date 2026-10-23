from fastapi import APIRouter

from . import core

router = APIRouter(prefix="/practitioner-roles", tags=["PractitionerRoles"])
router.include_router(core.router)
