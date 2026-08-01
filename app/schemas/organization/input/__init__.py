from .address import OrganizationAddressInput
from .alias import OrganizationAliasInput
from .contact import OrganizationContactInput, OrganizationContactTelecomInput
from .core import OrganizationCreateSchema, OrganizationPatchSchema
from .endpoint import OrganizationEndpointInput
from .identifier import OrganizationIdentifierInput
from .telecom import OrganizationTelecomInput
from .type import OrganizationTypeInput

__all__ = [
    "OrganizationCreateSchema",
    "OrganizationPatchSchema",
    "OrganizationIdentifierInput",
    "OrganizationTypeInput",
    "OrganizationAliasInput",
    "OrganizationTelecomInput",
    "OrganizationAddressInput",
    "OrganizationContactTelecomInput",
    "OrganizationContactInput",
    "OrganizationEndpointInput",
]
