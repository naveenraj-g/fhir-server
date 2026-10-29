from app.schemas.datatypes import CodingInput

from .core import LocationCreateSchema, LocationPatchSchema
from .endpoint import LocationEndpointInput
from .hours_of_operation import LocationHoursOfOperationInput
from .identifier import LocationIdentifierInput
from .telecom import LocationTelecomInput
from .type import LocationTypeInput

__all__ = [
    "CodingInput",
    "LocationCreateSchema",
    "LocationPatchSchema",
    "LocationIdentifierInput",
    "LocationTypeInput",
    "LocationTelecomInput",
    "LocationHoursOfOperationInput",
    "LocationEndpointInput",
]
