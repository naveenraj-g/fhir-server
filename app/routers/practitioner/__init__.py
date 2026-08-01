from fastapi import APIRouter

from . import (
    address,
    communication,
    core,
    identifier,
    name,
    photo,
    qualification,
    telecom,
)

router = APIRouter()

for _module in (
    core,
    name,
    identifier,
    telecom,
    address,
    photo,
    qualification,
    communication,
):
    router.include_router(_module.router)
