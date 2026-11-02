from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    Sequence,
    String,
)
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.enums import IdentifierUse, OrganizationReferenceType
from app.models.shared import TenantAuditMixin

specimen_definition_pub_seq = Sequence("specimen_definition_pub_seq", start=550000)


class SpecimenDefinitionModel(TenantAuditMixin, Base):
    """FHIR R4 SpecimenDefinition model.

    A kind of specimen with associated set of requirements.
    https://www.hl7.org/fhir/R4/specimendefinition.html
    """

    __tablename__ = "specimen_definition"

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)

    specimen_definition_id = Column(
        BigInteger,
        specimen_definition_pub_seq,
        server_default=specimen_definition_pub_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    # ── identifier (0..1 Identifier) — flattened ──────────────────────────
    identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    identifier_type_text = Column(String, nullable=True)
    identifier_system = Column(String, nullable=True)
    identifier_value = Column(String, nullable=True)
    identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    identifier_assigner_reference = Column(String, nullable=True)
    identifier_assigner_id = Column(BigInteger, nullable=True, index=True)
    identifier_assigner_type = Column(
        Enum(
            OrganizationReferenceType,
            name="organization_reference_type",
            create_type=False,
        ),
        nullable=True,
    )
    identifier_assigner_display = Column(String, nullable=True)

    identifier_assigner_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    identifier_assigner_identifier_type_system = Column(String, nullable=True)
    identifier_assigner_identifier_type_version = Column(String, nullable=True)
    identifier_assigner_identifier_type_code = Column(String, nullable=True)
    identifier_assigner_identifier_type_display = Column(String, nullable=True)
    identifier_assigner_identifier_type_text = Column(String, nullable=True)
    identifier_assigner_identifier_type_user_selected = Column(
        Boolean, nullable=True
    )
    identifier_assigner_identifier_system = Column(String, nullable=True)
    identifier_assigner_identifier_value = Column(String, nullable=True)
    identifier_assigner_identifier_period_start = Column(
        DateTime(timezone=True), nullable=True
    )
    identifier_assigner_identifier_period_end = Column(
        DateTime(timezone=True), nullable=True
    )

    # ── typeCollected (0..1 CodeableConcept) ─────────────────────────────
    type_collected_text = Column(String, nullable=True)

    # ── timeAspect (0..1 string) ──────────────────────────────────────────
    time_aspect = Column(String, nullable=True)

    # ── Relationships ─────────────────────────────────────────────────────
    identifier_type_codings = relationship(
        "SpecimenDefinitionIdentifierTypeCoding",
        back_populates="specimen_definition",
        cascade="all, delete-orphan",
    )
    type_collected_codings = relationship(
        "SpecimenDefinitionTypeCollectedCoding",
        back_populates="specimen_definition",
        cascade="all, delete-orphan",
    )
    patient_preparations = relationship(
        "SpecimenDefinitionPatientPreparation",
        back_populates="specimen_definition",
        cascade="all, delete-orphan",
    )
    collections = relationship(
        "SpecimenDefinitionCollection",
        back_populates="specimen_definition",
        cascade="all, delete-orphan",
    )
    types_tested = relationship(
        "SpecimenDefinitionTypeTested",
        back_populates="specimen_definition",
        cascade="all, delete-orphan",
    )
