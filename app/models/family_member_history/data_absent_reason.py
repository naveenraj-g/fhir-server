from sqlalchemy import BigInteger, Column, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class FamilyMemberHistoryDataAbsentReasonCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of FamilyMemberHistory.dataAbsentReason.coding (0..*)."""

    __tablename__ = "family_member_history_data_absent_reason_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    family_member_history_pk = Column(
        BigInteger, ForeignKey("family_member_history.id"), nullable=False, index=True
    )

    family_member_history = relationship(
        "FamilyMemberHistoryModel", back_populates="data_absent_reason_codings"
    )
