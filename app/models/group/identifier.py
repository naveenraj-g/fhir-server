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


class GroupIdentifier(TenantAuditMixin, Base):
    """Child table for Group.identifier[]."""

    __tablename__ = "group_identifier"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    group_pk = Column(
        BigInteger,
        ForeignKey("group.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    use = Column(
        Enum(
            IdentifierUse,
            name="group_identifier_use",
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

    group = relationship("GroupModel", back_populates="identifiers")
    type_codings = relationship(
        "GroupIdentifierTypeCoding",
        back_populates="identifier",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class GroupIdentifierTypeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """Grandchild table for Group.identifier[].type.coding[]."""

    __tablename__ = "group_identifier_type_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    identifier_id = Column(
        BigInteger,
        ForeignKey("group_identifier.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    identifier = relationship("GroupIdentifier", back_populates="type_codings")
