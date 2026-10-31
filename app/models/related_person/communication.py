from sqlalchemy import BigInteger, Boolean, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class RelatedPersonCommunication(TenantAuditMixin, Base):
    """RelatedPerson.communication (0..* BackboneElement) child table.
    Contains `language` (1..1 CodeableConcept) and `preferred` (0..1 boolean)."""

    __tablename__ = "related_person_communication"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    related_person_pk = Column(
        BigInteger, ForeignKey("related_person.id"), nullable=False, index=True
    )
    language_text = Column(String, nullable=True)
    preferred = Column(Boolean, nullable=True)

    related_person = relationship("RelatedPersonModel", back_populates="communications")
    language_codings = relationship(
        "RelatedPersonCommunicationLanguageCoding",
        back_populates="communication",
        cascade="all, delete-orphan",
    )


class RelatedPersonCommunicationLanguageCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of RelatedPerson.communication.language.coding (0..*)."""

    __tablename__ = "related_person_communication_language_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    related_person_communication_id = Column(
        BigInteger,
        ForeignKey("related_person_communication.id"),
        nullable=False,
        index=True,
    )

    communication = relationship(
        "RelatedPersonCommunication", back_populates="language_codings"
    )
