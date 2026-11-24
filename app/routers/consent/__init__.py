from fastapi import APIRouter

from . import core

router = APIRouter(prefix="/consents", tags=["Consents"])
router.include_router(core.router)
