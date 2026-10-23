from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin

# ---------------------------------------------------------------------------
# communication (0..*) CodeableConcept child table
# ---------------------------------------------------------------------------


class PractitionerCommunication(TenantAuditMixin, Base):
    """Practitioner.communication (0..* CodeableConcept) — languages the
    practitioner can use in patient communication. `text` stays flattened
    here (sibling of coding[], not part of it); coding[] is a real 0..*
    child table (PractitionerCommunicationCoding) — see
    app/models/organization/type.py for the full reasoning."""

    __tablename__ = "practitioner_communication"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    practitioner_pk = Column(
        BigInteger, ForeignKey("practitioner.id"), nullable=False, index=True
    )
    text = Column(String, nullable=True)

    practitioner = relationship("PractitionerModel", back_populates="communications")
    codings = relationship(
        "PractitionerCommunicationCoding",
        back_populates="communication",
        cascade="all, delete-orphan",
    )


class PractitionerCommunicationCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Practitioner.communication.coding (0..*)."""

    __tablename__ = "practitioner_communication_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    practitioner_communication_id = Column(
        BigInteger, ForeignKey("practitioner_communication.id"), nullable=False, index=True
    )

    communication = relationship("PractitionerCommunication", back_populates="codings")
