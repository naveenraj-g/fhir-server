from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class FamilyMemberHistoryReasonCode(TenantAuditMixin, Base):
    """FamilyMemberHistory.reasonCode (0..* CodeableConcept)."""

    __tablename__ = "family_member_history_reason_code"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    family_member_history_pk = Column(
        BigInteger, ForeignKey("family_member_history.id"), nullable=False, index=True
    )

    text = Column(String, nullable=True)

    family_member_history = relationship(
        "FamilyMemberHistoryModel", back_populates="reason_codes"
    )
    codings = relationship(
        "FamilyMemberHistoryReasonCodeCoding",
        back_populates="reason_code",
        cascade="all, delete-orphan",
    )


class FamilyMemberHistoryReasonCodeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of FamilyMemberHistory.reasonCode.coding (0..*)."""

    __tablename__ = "family_member_history_reason_code_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    family_member_history_reason_code_id = Column(
        BigInteger,
        ForeignKey("family_member_history_reason_code.id"),
        nullable=False,
        index=True,
    )

    reason_code = relationship(
        "FamilyMemberHistoryReasonCode", back_populates="codings"
    )
