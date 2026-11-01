from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class CommunicationReasonCode(TenantAuditMixin, Base):
    """Communication.reasonCode (0..*) child table."""

    __tablename__ = "communication_reason_code"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    communication_pk = Column(
        BigInteger,
        ForeignKey("communication.id"),
        nullable=False,
        index=True,
    )

    text = Column(String, nullable=True)

    communication = relationship(
        "CommunicationModel", back_populates="reason_codes"
    )
    codings = relationship(
        "CommunicationReasonCodeCoding",
        back_populates="reason_code",
        cascade="all, delete-orphan",
    )


class CommunicationReasonCodeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """Communication.reasonCode.coding (0..*) grandchild table."""

    __tablename__ = "communication_reason_code_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    communication_reason_code_id = Column(
        BigInteger,
        ForeignKey("communication_reason_code.id"),
        nullable=False,
        index=True,
    )

    reason_code = relationship(
        "CommunicationReasonCode", back_populates="codings"
    )
