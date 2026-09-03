from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import FHIRBase as Base
from app.models.enums import IdentifierUse, OrganizationReferenceType


class PractitionerQualification(Base):
    __tablename__ = "practitioner_qualification"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    practitioner_id = Column(
        BigInteger, ForeignKey("practitioner.id"), nullable=False, index=True
    )
    org_id = Column(String, nullable=False)

    # qualification.code (1..1 CodeableConcept — flattened)
    code_system = Column(String, nullable=True)
    code_code = Column(String, nullable=True)
    code_display = Column(String, nullable=True)
    code_text = Column(String, nullable=True)

    # qualification.status (0..1 CodeableConcept — flattened)
    status_system = Column(String, nullable=True)
    status_code = Column(String, nullable=True)
    status_display = Column(String, nullable=True)
    status_text = Column(String, nullable=True)

    # qualification.period (0..1)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    # qualification.issuer (0..1 Reference(Organization) — flattened)
    issuer_type = Column(
        Enum(
            OrganizationReferenceType,
            name="organization_reference_type",
            create_type=False,
        ),
        nullable=True,
    )
    issuer_id = Column(BigInteger, nullable=True, index=True)
    issuer_display = Column(String, nullable=True)

    # issuer.identifier (0..1 Identifier) — logical-reference fallback for
    # when the issuing organization isn't a resource in this system
    issuer_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use"), nullable=True
    )
    issuer_identifier_type_system = Column(String, nullable=True)
    issuer_identifier_type_version = Column(String, nullable=True)
    issuer_identifier_type_code = Column(String, nullable=True)
    issuer_identifier_type_display = Column(String, nullable=True)
    issuer_identifier_type_text = Column(String, nullable=True)
    issuer_identifier_type_user_selected = Column(Boolean, nullable=True)
    issuer_identifier_system = Column(String, nullable=True)
    issuer_identifier_value = Column(String, nullable=True)
    issuer_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    issuer_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, nullable=False)
    updated_by = Column(String, nullable=True)

    practitioner = relationship("PractitionerModel", back_populates="qualifications")
    identifiers = relationship(
        "PractitionerQualificationIdentifier",
        back_populates="qualification",
        cascade="all, delete-orphan",
    )


class PractitionerQualificationIdentifier(Base):
    """qualification.identifier[] — Identifier — identifiers for this qualification (e.g. license number)."""

    __tablename__ = "practitioner_qualification_identifier"
    __table_args__ = (
        UniqueConstraint(
            "system",
            "value",
            name="uq_practitioner_qualification_identifier_system_value",
        ),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    qualification_id = Column(
        BigInteger, ForeignKey("practitioner_qualification.id"), nullable=False, index=True
    )
    org_id = Column(String, nullable=False)

    use = Column(Enum(IdentifierUse, name="identifier_use"), nullable=True)
    # Identifier.type is a CodeableConcept — single coding flattened + text
    type_system = Column(String, nullable=True)
    type_version = Column(String, nullable=True)
    type_code = Column(String, nullable=True)
    type_display = Column(String, nullable=True)
    type_text = Column(String, nullable=True)
    type_user_selected = Column(Boolean, nullable=True)
    system = Column(String, nullable=False)
    value = Column(String, nullable=False)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    # assigner (0..1 Reference(Organization)) — resolved reference, same
    # convention as PractitionerIdentifier.assigner_*
    assigner_type = Column(
        Enum(
            OrganizationReferenceType,
            name="organization_reference_type",
            create_type=False,
        ),
        nullable=True,
    )
    assigner_id = Column(BigInteger, nullable=True, index=True)
    assigner_display = Column(String, nullable=True)

    # assigner.identifier (0..1 Identifier) — logical-reference fallback for
    # when the assigning organization isn't a resource in this system
    assigner_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use"), nullable=True
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

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, nullable=False)
    updated_by = Column(String, nullable=True)

    qualification = relationship(
        "PractitionerQualification", back_populates="identifiers"
    )
