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
from app.models.group.enums import GroupMemberEntityReferenceType
from app.models.shared.tenant_audit import TenantAuditMixin


class GroupMember(TenantAuditMixin, Base):
    """Child table for Group.member[]."""

    __tablename__ = "group_member"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    group_pk = Column(
        BigInteger,
        ForeignKey("group.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    entity_reference = Column(String, nullable=False)
    entity_type = Column(
        Enum(
            GroupMemberEntityReferenceType,
            name="group_member_entity_reference_type",
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=True,
    )
    entity_id = Column(BigInteger, nullable=True)
    entity_display = Column(String, nullable=True)

    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)
    inactive = Column(Boolean, nullable=True)

    group = relationship("GroupModel", back_populates="members")
