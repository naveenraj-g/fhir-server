from fastapi import APIRouter

from . import core

router = APIRouter(prefix="/validate", tags=["FHIR Validation"])
router.include_router(core.router)
