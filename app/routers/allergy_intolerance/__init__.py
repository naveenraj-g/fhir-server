from fastapi import APIRouter

from . import core

router = APIRouter(prefix="/allergy-intolerances", tags=["AllergyIntolerances"])
router.include_router(core.router)
