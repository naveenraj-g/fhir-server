from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Enum,
    Integer,
    Sequence,
    String,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.group.enums import (
    GroupManagingEntityReferenceType,
    GroupType,
)
from app.models.shared.tenant_audit import TenantAuditMixin


class GroupModel(TenantAuditMixin, Base):
    """SQLAlchemy ORM model for FHIR R4 Group resource."""

    __tablename__ = "group"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    group_id = Column(
        BigInteger,
        Sequence(
            "group_pub_seq",
            start=430000,
            increment=1,
            metadata=Base.metadata,
        ),
        unique=True,
        index=True,
        nullable=False,
    )

    active = Column(Boolean, nullable=True)
    type = Column(
        Enum(
            GroupType,
            name="group_type",
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=False,
    )
    actual = Column(Boolean, nullable=False)
    code_text = Column(String, nullable=True)
    name = Column(String, nullable=True)
    quantity = Column(Integer, nullable=True)

    managing_entity_reference = Column(String, nullable=True)
    managing_entity_type = Column(
        Enum(
            GroupManagingEntityReferenceType,
            name="group_managing_entity_reference_type",
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=True,
    )
    managing_entity_id = Column(BigInteger, nullable=True)
    managing_entity_display = Column(String, nullable=True)

    extension = Column(JSONB, nullable=False, server_default="[]")

    # Relationships
    identifiers = relationship(
        "GroupIdentifier",
        back_populates="group",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    code_codings = relationship(
        "GroupCodeCoding",
        back_populates="group",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    characteristics = relationship(
        "GroupCharacteristic",
        back_populates="group",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    members = relationship(
        "GroupMember",
        back_populates="group",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
