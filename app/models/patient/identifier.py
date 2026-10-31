from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    String,
)
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.enums import IdentifierUse, OrganizationReferenceType
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class PatientIdentifier(TenantAuditMixin, Base):
    """Patient.identifier (0..*) child table.
    No UniqueConstraint on (system, value) and no DB-level CHECK constraints —
    same reasoning as OrganizationIdentifier / PractitionerIdentifier."""

    __tablename__ = "patient_identifier"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    patient_pk = Column(
        BigInteger, ForeignKey("patient.id"), nullable=False, index=True
    )

    use = Column(Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True)
    type_text = Column(String, nullable=True)
    system = Column(String, nullable=True)
    value = Column(String, nullable=True)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    # assigner (0..1 Reference(Organization))
    assigner_reference = Column(String, nullable=True)
    assigner_id = Column(BigInteger, nullable=True, index=True)
    assigner_type = Column(
        Enum(
            OrganizationReferenceType,
            name="organization_reference_type",
            create_type=False,
        ),
        nullable=True,
    )
    assigner_display = Column(String, nullable=True)

    # assigner.identifier fallback
    assigner_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    assigner_identifier_type_system = Column(String, nullable=True)
    assigner_identifier_type_version = Column(String, nullable=True)
    assigner_identifier_type_code = Column(String, nullable=True)
    assigner_identifier_type_display = Column(String, nullable=True)
    assigner_identifier_type_text = Column(String, nullable=True)
    assigner_identifier_type_user_selected = Column(Boolean, nullable=True)
    assigner_identifier_system = Column(String, nullable=True)
    assigner_identifier_value = Column(String, nullable=True)
    assigner_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    assigner_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    patient = relationship("PatientModel", back_populates="identifiers")
    type_codings = relationship(
        "PatientIdentifierTypeCoding",
        back_populates="identifier",
        cascade="all, delete-orphan",
    )


class PatientIdentifierTypeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Patient.identifier.type.coding (0..*)."""

    __tablename__ = "patient_identifier_type_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    patient_identifier_id = Column(
        BigInteger, ForeignKey("patient_identifier.id"), nullable=False, index=True
    )

    identifier = relationship("PatientIdentifier", back_populates="type_codings")
