from fastapi import APIRouter

from . import core

router = APIRouter(prefix="/questionnaire-responses", tags=["QuestionnaireResponses"])
router.include_router(core.router)
