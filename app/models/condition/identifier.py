from sqlalchemy import (
    BigInteger,
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


class ConditionIdentifier(TenantAuditMixin, Base):
    """Condition.identifier (0..*) child table."""

    __tablename__ = "condition_identifier"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    condition_pk = Column(
        BigInteger, ForeignKey("condition.id"), nullable=False, index=True
    )

    use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
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
    assigner_identifier_system = Column(String, nullable=True)
    assigner_identifier_value = Column(String, nullable=True)
    assigner_identifier_type_text = Column(String, nullable=True)

    condition = relationship("ConditionModel", back_populates="identifiers")
    type_codings = relationship(
        "ConditionIdentifierTypeCoding",
        back_populates="identifier",
        cascade="all, delete-orphan",
    )


class ConditionIdentifierTypeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Condition.identifier.type.coding (0..*)."""

    __tablename__ = "condition_identifier_type_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    condition_identifier_id = Column(
        BigInteger,
        ForeignKey("condition_identifier.id"),
        nullable=False,
        index=True,
    )

    identifier = relationship("ConditionIdentifier", back_populates="type_codings")
