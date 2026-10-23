from app.schemas.datatypes import CodingInput
from .core import SlotCreateSchema, SlotPatchSchema
from .identifier import SlotIdentifierInput
from .service_category import SlotServiceCategoryInput
from .service_type import SlotServiceTypeInput
from .specialty import SlotSpecialtyInput

__all__ = [
    "CodingInput",
    "SlotCreateSchema",
    "SlotIdentifierInput",
    "SlotPatchSchema",
    "SlotServiceCategoryInput",
    "SlotServiceTypeInput",
    "SlotSpecialtyInput",
]
