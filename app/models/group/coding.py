from sqlalchemy import BigInteger, Column, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class GroupCodeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """Child table for Group.code.coding[]."""

    __tablename__ = "group_code_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    group_pk = Column(
        BigInteger,
        ForeignKey("group.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    group = relationship("GroupModel", back_populates="code_codings")
