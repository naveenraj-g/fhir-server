from .alias import LocationAliasInput
from .core import LocationCreateSchema, LocationPatchSchema
from .endpoint import LocationEndpointInput
from .hours_of_operation import LocationHoursOfOperationInput
from .identifier import LocationIdentifierInput
from .telecom import LocationTelecomInput
from .type import LocationTypeInput

__all__ = [
    "LocationCreateSchema",
    "LocationPatchSchema",
    "LocationIdentifierInput",
    "LocationTypeInput",
    "LocationAliasInput",
    "LocationTelecomInput",
    "LocationHoursOfOperationInput",
    "LocationEndpointInput",
]
