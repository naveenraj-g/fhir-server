from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.enums import IdentifierUse
from app.models.immunization.enums import (
    ImmunizationProtocolAppliedAuthorityReferenceType,
)
from app.models.shared import TenantAuditMixin
from app.models.shared.datatypes import FhirCodingMixin


class ImmunizationProtocolAppliedModel(TenantAuditMixin, Base):
    """Immunization.protocolApplied (0..* BackboneElement) child table."""

    __tablename__ = "immunization_protocol_applied"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    immunization_pk = Column(
        BigInteger, ForeignKey("immunization.id"), nullable=False, index=True
    )

    series = Column(String, nullable=True)

    # authority (0..1 Reference(Organization))
    authority_reference = Column(String, nullable=True)
    authority_type = Column(
        Enum(
            ImmunizationProtocolAppliedAuthorityReferenceType,
            name="immunization_protocol_applied_authority_reference_type",
        ),
        nullable=True,
    )
    authority_id = Column(BigInteger, nullable=True, index=True)
    authority_display = Column(String, nullable=True)

    # authority.identifier fallback (11 columns)
    authority_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    authority_identifier_type_system = Column(String, nullable=True)
    authority_identifier_type_version = Column(String, nullable=True)
    authority_identifier_type_code = Column(String, nullable=True)
    authority_identifier_type_display = Column(String, nullable=True)
    authority_identifier_type_user_selected = Column(Boolean, nullable=True)
    authority_identifier_type_text = Column(String, nullable=True)
    authority_identifier_system = Column(String, nullable=True)
    authority_identifier_value = Column(String, nullable=True)
    authority_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    authority_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    dose_number_positive_int = Column(Integer, nullable=True)
    dose_number_string = Column(String, nullable=True)
    series_doses_positive_int = Column(Integer, nullable=True)
    series_doses_string = Column(String, nullable=True)

    immunization = relationship(
        "ImmunizationModel", back_populates="protocol_applied_items"
    )
    target_diseases = relationship(
        "ImmunizationProtocolAppliedTargetDiseaseModel",
        back_populates="protocol_applied",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class ImmunizationProtocolAppliedTargetDiseaseModel(TenantAuditMixin, Base):
    """Immunization.protocolApplied.targetDisease (0..* CodeableConcept) grandchild table."""

    __tablename__ = "immunization_protocol_applied_target_disease"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    protocol_applied_id = Column(
        BigInteger,
        ForeignKey("immunization_protocol_applied.id"),
        nullable=False,
        index=True,
    )

    text = Column(String, nullable=True)

    protocol_applied = relationship(
        "ImmunizationProtocolAppliedModel", back_populates="target_diseases"
    )
    codings = relationship(
        "ImmunizationProtocolAppliedTargetDiseaseCodingModel",
        back_populates="target_disease",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class ImmunizationProtocolAppliedTargetDiseaseCodingModel(
    FhirCodingMixin, TenantAuditMixin, Base
):
    """Immunization.protocolApplied.targetDisease.coding (0..* Coding) great-grandchild table."""

    __tablename__ = "immunization_protocol_applied_target_disease_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    target_disease_id = Column(
        BigInteger,
        ForeignKey("immunization_protocol_applied_target_disease.id"),
        nullable=False,
        index=True,
    )

    target_disease = relationship(
        "ImmunizationProtocolAppliedTargetDiseaseModel", back_populates="codings"
    )
