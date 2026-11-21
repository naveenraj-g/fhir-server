from fastapi import APIRouter

from . import core

router = APIRouter(prefix="/clinical-impressions", tags=["ClinicalImpressions"])
router.include_router(core.router)
