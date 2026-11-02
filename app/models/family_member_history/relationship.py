from sqlalchemy import BigInteger, Column, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class FamilyMemberHistoryRelationshipCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of FamilyMemberHistory.relationship.coding (0..*)."""

    __tablename__ = "family_member_history_relationship_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    family_member_history_pk = Column(
        BigInteger, ForeignKey("family_member_history.id"), nullable=False, index=True
    )

    family_member_history = relationship(
        "FamilyMemberHistoryModel", back_populates="relationship_codings"
    )
