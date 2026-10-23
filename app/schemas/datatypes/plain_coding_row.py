from pydantic import Field

from app.schemas.datatypes.audit_fields import AuditFields
from app.schemas.datatypes.plain_coding import PlainCoding


class PlainCodingRow(PlainCoding, AuditFields):
    """One stored `coding[]` row — PlainCoding's fields plus the row's own
    DB identity and audit trail. Shared by every resource's CodeableConcept
    coding child tables (Organization.type, Location.physicalType,
    HealthcareService.category, ...)."""

    id: int = Field(..., description="Internal row ID.")
