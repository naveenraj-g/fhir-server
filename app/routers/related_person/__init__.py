from fastapi import APIRouter

from . import core

router = APIRouter(prefix="/related-persons", tags=["RelatedPersons"])
router.include_router(core.router)
