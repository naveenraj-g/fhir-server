from fastapi import APIRouter

from . import (
    address,
    communication,
    contact,
    core,
    general_practitioner,
    identifier,
    link,
    name,
    photo,
    telecom,
)

router = APIRouter(prefix="/patients", tags=["Patients"])

for _module in (
    core,
    name,
    identifier,
    telecom,
    address,
    photo,
    contact,
    communication,
    general_practitioner,
    link,
):
    router.include_router(_module.router)
