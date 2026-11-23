from fastapi import APIRouter

from . import core

router = APIRouter(prefix="/document-references", tags=["DocumentReferences"])
router.include_router(core.router)
