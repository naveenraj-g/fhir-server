from sqlalchemy import BigInteger, Boolean, Column, DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.document_reference.enums import DocumentReferenceContextEncounterReferenceType
from app.models.enums import IdentifierUse
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class DocumentReferenceContextEncounter(TenantAuditMixin, Base):
    """DocumentReference.context.encounter (0..*) Reference(Encounter | EpisodeOfCare)."""

    __tablename__ = "document_reference_context_encounter"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    document_reference_pk = Column(
        BigInteger, ForeignKey("document_reference.id"), nullable=False, index=True
    )

    reference_reference = Column(String, nullable=True)
    reference_type = Column(
        Enum(
            DocumentReferenceContextEncounterReferenceType,
            name="document_reference_context_encounter_reference_type",
        ),
        nullable=True,
    )
    reference_id = Column(BigInteger, nullable=True, index=True)
    reference_display = Column(String, nullable=True)
    reference_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    reference_identifier_type_system = Column(String, nullable=True)
    reference_identifier_type_version = Column(String, nullable=True)
    reference_identifier_type_code = Column(String, nullable=True)
    reference_identifier_type_display = Column(String, nullable=True)
    reference_identifier_type_user_selected = Column(Boolean, nullable=True)
    reference_identifier_type_text = Column(String, nullable=True)
    reference_identifier_system = Column(String, nullable=True)
    reference_identifier_value = Column(String, nullable=True)
    reference_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    reference_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    document_reference = relationship("DocumentReferenceModel", back_populates="context_encounters")


class DocumentReferenceContextEvent(TenantAuditMixin, Base):
    """DocumentReference.context.event (0..*) CodeableConcept."""

    __tablename__ = "document_reference_context_event"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    document_reference_pk = Column(
        BigInteger, ForeignKey("document_reference.id"), nullable=False, index=True
    )

    text = Column(String, nullable=True)

    document_reference = relationship("DocumentReferenceModel", back_populates="context_events")
    codings = relationship(
        "DocumentReferenceContextEventCoding",
        back_populates="event",
        cascade="all, delete-orphan",
    )


class DocumentReferenceContextEventCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of DocumentReference.context.event.coding (0..*)."""

    __tablename__ = "document_reference_context_event_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    document_reference_context_event_id = Column(
        BigInteger,
        ForeignKey("document_reference_context_event.id"),
        nullable=False,
        index=True,
    )

    event = relationship("DocumentReferenceContextEvent", back_populates="codings")


class DocumentReferenceContextRelated(TenantAuditMixin, Base):
    """DocumentReference.context.related (0..*) Reference(Any)."""

    __tablename__ = "document_reference_context_related"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    document_reference_pk = Column(
        BigInteger, ForeignKey("document_reference.id"), nullable=False, index=True
    )

    reference_reference = Column(String, nullable=True)
    reference_type = Column(String, nullable=True)
    reference_id = Column(BigInteger, nullable=True, index=True)
    reference_display = Column(String, nullable=True)
    reference_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    reference_identifier_type_system = Column(String, nullable=True)
    reference_identifier_type_version = Column(String, nullable=True)
    reference_identifier_type_code = Column(String, nullable=True)
    reference_identifier_type_display = Column(String, nullable=True)
    reference_identifier_type_user_selected = Column(Boolean, nullable=True)
    reference_identifier_type_text = Column(String, nullable=True)
    reference_identifier_system = Column(String, nullable=True)
    reference_identifier_value = Column(String, nullable=True)
    reference_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    reference_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    document_reference = relationship("DocumentReferenceModel", back_populates="context_related")
