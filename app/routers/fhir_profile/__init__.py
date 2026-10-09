from fastapi import APIRouter

from . import core

router = APIRouter(prefix="/fhir-profiles", tags=["FHIR Profiles"])
router.include_router(core.router)
