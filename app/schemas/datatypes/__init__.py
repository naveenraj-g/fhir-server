"""
Re-exports every shared FHIR R4 datatype (plus their plain/snake_case
counterparts) as `app.schemas.datatypes.*` so callers don't need to know
which file a given type lives in.

Each datatype gets its own module (one class per file) so a resource that
needs a field description tweaked, or a stricter validator, can subclass
the specific type it needs without touching the others — mirrors
fhir-gql's app.fhir.schemas.datatypes package.
"""

from app.schemas.datatypes.address import FHIRAddress
from app.schemas.datatypes.attachment import FHIRAttachment
from app.schemas.datatypes.attachment_input import AttachmentInput
from app.schemas.datatypes.audit_fields import AuditFields
from app.schemas.datatypes.bundle import FHIRBundle
from app.schemas.datatypes.bundle_entry import FHIRBundleEntry
from app.schemas.datatypes.codeable_concept import FHIRCodeableConcept
from app.schemas.datatypes.coding import FHIRCoding
from app.schemas.datatypes.coding_input import CodingInput
from app.schemas.datatypes.contact_point import FHIRContactPoint
from app.schemas.datatypes.contact_point_input import ContactPointInput
from app.schemas.datatypes.human_name import FHIRHumanName
from app.schemas.datatypes.human_name_input import HumanNameInput
from app.schemas.datatypes.identifier import FHIRIdentifier
from app.schemas.datatypes.meta import FHIRMeta
from app.schemas.datatypes.period import FHIRPeriod
from app.schemas.datatypes.plain_attachment_row import PlainAttachmentRow
from app.schemas.datatypes.plain_coding import PlainCoding
from app.schemas.datatypes.plain_coding_row import PlainCodingRow
from app.schemas.datatypes.plain_contact_point_row import PlainContactPointRow
from app.schemas.datatypes.plain_human_name_row import PlainHumanNameRow
from app.schemas.datatypes.plain_identifier import PlainIdentifier
from app.schemas.datatypes.plain_identifier_type import PlainIdentifierType
from app.schemas.datatypes.plain_reason_code import PlainReasonCode
from app.schemas.datatypes.reference import FHIRReference

__all__ = [
    "AttachmentInput",
    "AuditFields",
    "CodingInput",
    "ContactPointInput",
    "FHIRAddress", "FHIRAttachment", "FHIRBundle", "FHIRBundleEntry", "FHIRCoding", "FHIRCodeableConcept",
    "FHIRContactPoint", "FHIRHumanName", "FHIRIdentifier", "FHIRMeta", "FHIRPeriod", "FHIRReference",
    "HumanNameInput",
    "PlainAttachmentRow", "PlainCoding", "PlainCodingRow", "PlainContactPointRow", "PlainHumanNameRow",
    "PlainIdentifier", "PlainIdentifierType", "PlainReasonCode",
]
