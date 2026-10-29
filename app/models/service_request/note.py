from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.service_request.enums import ServiceRequestNoteAuthorReferenceType
from app.models.shared import TenantAuditMixin

# ---------------------------------------------------------------------------
# note (0..*) Annotation child table — this codebase's first use of the
# FHIR Annotation datatype
# ---------------------------------------------------------------------------


class ServiceRequestNote(TenantAuditMixin, Base):
    """ServiceRequest.note (0..* Annotation) —
    https://www.hl7.org/fhir/R4/datatypes.html#Annotation

    `author[x]` (0..1, choice of Reference(Practitioner|Patient|
    RelatedPerson|Organization) | string) — the Reference variant is
    flattened with the standard shape minus the identifier fallback
    (same scope decision as Questionnaire.item.initial's own
    value_reference — a minor choice-type variant, not a dedicated
    top-level Reference field). `text` (markdown, 1..1 required by spec)
    stays nullable at the DB layer, like every other "required" field in
    this codebase — enforced by the FHIR validator, not a DB constraint.
    """

    __tablename__ = "service_request_note"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    service_request_pk = Column(
        BigInteger, ForeignKey("service_request.id"), nullable=False, index=True
    )

    author_string = Column(String, nullable=True)
    author_reference = Column(String, nullable=True)
    author_type = Column(
        Enum(ServiceRequestNoteAuthorReferenceType, name="service_request_note_author_reference_type"),
        nullable=True,
    )
    author_id = Column(BigInteger, nullable=True, index=True)
    author_display = Column(String, nullable=True)

    time = Column(DateTime(timezone=True), nullable=True)
    text = Column(Text, nullable=True)

    service_request = relationship("ServiceRequestModel", back_populates="notes")
