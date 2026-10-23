from app.schemas.slot.input import (
    SlotCreateSchema,
    SlotIdentifierInput,
    SlotPatchSchema,
    SlotServiceCategoryInput,
    SlotServiceTypeInput,
    SlotSpecialtyInput,
)
from app.schemas.slot.response import (
    FHIRSlotBundle,
    FHIRSlotBundleEntry,
    FHIRSlotSchema,
    PaginatedSlotResponse,
    PlainSlotIdentifier,
    PlainSlotResponse,
    PlainSlotServiceCategory,
    PlainSlotServiceType,
    PlainSlotSpecialty,
)

__all__ = [
    "FHIRSlotBundle",
    "FHIRSlotBundleEntry",
    "FHIRSlotSchema",
    "PaginatedSlotResponse",
    "PlainSlotIdentifier",
    "PlainSlotResponse",
    "PlainSlotServiceCategory",
    "PlainSlotServiceType",
    "PlainSlotSpecialty",
    "SlotCreateSchema",
    "SlotIdentifierInput",
    "SlotPatchSchema",
    "SlotServiceCategoryInput",
    "SlotServiceTypeInput",
    "SlotSpecialtyInput",
]
