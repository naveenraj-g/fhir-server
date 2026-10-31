from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class CommunicationRequestReasonCode(TenantAuditMixin, Base):
    """CommunicationRequest.reasonCode (0..*) child table."""

    __tablename__ = "communication_request_reason_code"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    communication_request_pk = Column(
        BigInteger,
        ForeignKey("communication_request.id"),
        nullable=False,
        index=True,
    )

    text = Column(String, nullable=True)

    communication_request = relationship(
        "CommunicationRequestModel", back_populates="reason_codes"
    )
    codings = relationship(
        "CommunicationRequestReasonCodeCoding",
        back_populates="reason_code",
        cascade="all, delete-orphan",
    )


class CommunicationRequestReasonCodeCoding(
    FhirCodingMixin, TenantAuditMixin, Base
):
    """CommunicationRequest.reasonCode.coding (0..*) grandchild table."""

    __tablename__ = "communication_request_reason_code_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    communication_request_reason_code_id = Column(
        BigInteger,
        ForeignKey("communication_request_reason_code.id"),
        nullable=False,
        index=True,
    )

    reason_code = relationship(
        "CommunicationRequestReasonCode", back_populates="codings"
    )
