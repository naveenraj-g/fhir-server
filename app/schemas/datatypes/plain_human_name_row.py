from typing import List, Optional
from pydantic import Field

from app.schemas.datatypes.audit_fields import AuditFields


class PlainHumanNameRow(AuditFields):
    """One stored HumanName row — plain/snake_case rendering plus the row's
    own DB identity and audit trail. Shared by every resource's `name[]`
    child table (Practitioner.name, ...)."""

    id: int = Field(..., description="Internal row ID.")
    use: Optional[str] = Field(
        None, description="Identifies the purpose of this name."
    )
    text: Optional[str] = Field(
        None, description="Text representation of the full name, as it would normally be displayed."
    )
    family: Optional[str] = Field(None, description="Family name (often called 'surname').")
    given: Optional[List[str]] = Field(None, description="Given name(s).")
    prefix: Optional[List[str]] = Field(None, description="Name prefix(es) (e.g. titles).")
    suffix: Optional[List[str]] = Field(None, description="Name suffix(es).")
    period_start: Optional[str] = Field(
        None, description="Start of the period during which this name was/is in use."
    )
    period_end: Optional[str] = Field(
        None, description="End of the period during which this name was/is in use."
    )
