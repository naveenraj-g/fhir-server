from app.schemas.slot.input import SlotCreateSchema, SlotPatchSchema
from app.schemas.slot.response import FHIRSlotBundle, FHIRSlotBundleEntry, FHIRSlotSchema

__all__ = [
    "FHIRSlotBundle",
    "FHIRSlotBundleEntry",
    "FHIRSlotSchema",
    "SlotCreateSchema",
    "SlotPatchSchema",
]
