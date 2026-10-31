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


class ConsentIdentifier(TenantAuditMixin, Base):
    """Child table for Consent.identifier[]."""

    __tablename__ = "consent_identifier"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    consent_pk = Column(
        BigInteger,
        ForeignKey("consent.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    use = Column(
        Enum(
            IdentifierUse,
            name="consent_identifier_use",
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=True,
    )
    type_text = Column(String, nullable=True)
    system = Column(String, nullable=True)
    value = Column(String, nullable=True)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    assigner_reference = Column(String, nullable=True)
    assigner_type = Column(
        Enum(
            OrganizationReferenceType,
            name="organization_reference_type",
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
            create_type=False,
        ),
        nullable=True,
    )
    assigner_id = Column(BigInteger, nullable=True)
    assigner_display = Column(String, nullable=True)

    consent = relationship("ConsentModel", back_populates="identifiers")
    type_codings = relationship(
        "ConsentIdentifierTypeCoding",
        back_populates="identifier",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class ConsentIdentifierTypeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """Grandchild table for Consent.identifier[].type.coding[]."""

    __tablename__ = "consent_identifier_type_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    identifier_id = Column(
        BigInteger,
        ForeignKey("consent_identifier.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    identifier = relationship("ConsentIdentifier", back_populates="type_codings")
