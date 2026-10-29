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
# identifier (0..*) child table
# ---------------------------------------------------------------------------


class QuestionnaireIdentifier(TenantAuditMixin, Base):
    """Questionnaire.identifier (0..*) — mirrors
    app.models.organization.identifier.OrganizationIdentifier field-for-
    field; see that class's docstring for the full reasoning (no uniqueness
    constraint, no DB CHECKs, assigner's four flattened Reference(Organization)
    columns plus its own Identifier logical-reference fallback)."""

    __tablename__ = "questionnaire_identifier"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    questionnaire_pk = Column(
        BigInteger, ForeignKey("questionnaire.id"), nullable=False, index=True
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

    questionnaire = relationship("QuestionnaireModel", back_populates="identifiers")
    type_codings = relationship(
        "QuestionnaireIdentifierTypeCoding",
        back_populates="identifier",
        cascade="all, delete-orphan",
    )


# ---------------------------------------------------------------------------
# identifier.type.coding (0..*) grandchild table
# ---------------------------------------------------------------------------


class QuestionnaireIdentifierTypeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Questionnaire.identifier.type.coding (0..*)."""

    __tablename__ = "questionnaire_identifier_type_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    questionnaire_identifier_id = Column(
        BigInteger, ForeignKey("questionnaire_identifier.id"), nullable=False, index=True
    )

    identifier = relationship("QuestionnaireIdentifier", back_populates="type_codings")
