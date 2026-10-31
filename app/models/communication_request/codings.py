from sqlalchemy import BigInteger, Column, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class CommunicationRequestStatusReasonCoding(
    FhirCodingMixin, TenantAuditMixin, Base
):
    """CommunicationRequest.statusReason.coding (0..*) child table."""

    __tablename__ = "communication_request_status_reason_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    communication_request_pk = Column(
        BigInteger,
        ForeignKey("communication_request.id"),
        nullable=False,
        index=True,
    )

    communication_request = relationship(
        "CommunicationRequestModel", back_populates="status_reason_codings"
    )
