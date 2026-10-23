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

# ---------------------------------------------------------------------------
# qualification (0..*) BackboneElement child table
# ---------------------------------------------------------------------------


class PractitionerQualification(TenantAuditMixin, Base):
    """Practitioner.qualification[] — certifications, licenses, or training.

    `code` (1..1 CodeableConcept) is REQUIRED per spec, but — same
    architecture choice as every other R4 rule in this project (see
    OrganizationModel's docstring, app/models/organization/core.py) — that
    requirement is enforced at the application/validator layer (the input
    schema's `code_coding`/`code_text` aren't Optional), not as a DB NOT
    NULL here: `code_text` stays nullable like every other flattened
    CodeableConcept.text column, since a CodeableConcept can be satisfied by
    text alone, coding alone, or both."""

    __tablename__ = "practitioner_qualification"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    # Containment FK — see identifier.py's practitioner_pk for why this
    # isn't named practitioner_id.
    practitioner_pk = Column(
        BigInteger, ForeignKey("practitioner.id"), nullable=False, index=True
    )

    # code (1..1 CodeableConcept) — code_text stays flattened (sibling of
    # coding[], not part of it); code's coding[] is a real 0..* child table
    # (PractitionerQualificationCodeCoding).
    code_text = Column(String, nullable=True)

    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    # issuer (0..1 Reference(Organization)) — flattened, no FK, stores the
    # PUBLIC organization_id — see app/models/organization/core.py's
    # partof_* columns for the full reasoning.
    issuer_reference = Column(String, nullable=True)
    issuer_id = Column(BigInteger, nullable=True, index=True)
    issuer_type = Column(
        Enum(
            OrganizationReferenceType,
            name="organization_reference_type",
            create_type=False,
        ),
        nullable=True,
    )
    issuer_display = Column(String, nullable=True)

    # issuer.identifier (0..1 Identifier) — logical-reference fallback
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

    practitioner = relationship("PractitionerModel", back_populates="qualifications")
    identifiers = relationship(
        "PractitionerQualificationIdentifier",
        back_populates="qualification",
        cascade="all, delete-orphan",
    )
    code_codings = relationship(
        "PractitionerQualificationCodeCoding",
        back_populates="qualification",
        cascade="all, delete-orphan",
    )


# ---------------------------------------------------------------------------
# qualification.code.coding (0..*) grandchild table
# ---------------------------------------------------------------------------


class PractitionerQualificationCodeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Practitioner.qualification.code.coding (0..*)."""

    __tablename__ = "practitioner_qualification_code_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    practitioner_qualification_id = Column(
        BigInteger, ForeignKey("practitioner_qualification.id"), nullable=False, index=True
    )

    qualification = relationship(
        "PractitionerQualification", back_populates="code_codings"
    )


# ---------------------------------------------------------------------------
# qualification.identifier (0..*) grandchild table
# ---------------------------------------------------------------------------


class PractitionerQualificationIdentifier(TenantAuditMixin, Base):
    """One entry of Practitioner.qualification.identifier (0..*)."""

    __tablename__ = "practitioner_qualification_identifier"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    practitioner_qualification_id = Column(
        BigInteger, ForeignKey("practitioner_qualification.id"), nullable=False, index=True
    )

    use = Column(Enum(IdentifierUse, name="identifier_use"), nullable=True)
    type_text = Column(String, nullable=True)
    system = Column(String, nullable=True)
    value = Column(String, nullable=True)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

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

    qualification = relationship(
        "PractitionerQualification", back_populates="identifiers"
    )
    type_codings = relationship(
        "PractitionerQualificationIdentifierTypeCoding",
        back_populates="identifier",
        cascade="all, delete-orphan",
    )


# ---------------------------------------------------------------------------
# qualification.identifier.type.coding (0..*) great-grandchild table
# ---------------------------------------------------------------------------


class PractitionerQualificationIdentifierTypeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Practitioner.qualification.identifier.type.coding (0..*)."""

    __tablename__ = "practitioner_qualification_identifier_type_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    practitioner_qualification_identifier_id = Column(
        BigInteger,
        ForeignKey("practitioner_qualification_identifier.id"),
        nullable=False,
        index=True,
    )

    identifier = relationship(
        "PractitionerQualificationIdentifier", back_populates="type_codings"
    )
