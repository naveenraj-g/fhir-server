from sqlalchemy import BigInteger, Column, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class CommunicationStatusReasonCoding(
    FhirCodingMixin, TenantAuditMixin, Base
):
    """Communication.statusReason.coding (0..*) child table."""

    __tablename__ = "communication_status_reason_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    communication_pk = Column(
        BigInteger,
        ForeignKey("communication.id"),
        nullable=False,
        index=True,
    )

    communication = relationship(
        "CommunicationModel", back_populates="status_reason_codings"
    )


class CommunicationTopicCoding(
    FhirCodingMixin, TenantAuditMixin, Base
):
    """Communication.topic.coding (0..*) child table."""

    __tablename__ = "communication_topic_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    communication_pk = Column(
        BigInteger,
        ForeignKey("communication.id"),
        nullable=False,
        index=True,
    )

    communication = relationship(
        "CommunicationModel", back_populates="topic_codings"
    )
