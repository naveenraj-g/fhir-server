from fastapi import APIRouter

from . import core

router = APIRouter(prefix="/plan-definitions", tags=["PlanDefinitions"])
router.include_router(core.router)
