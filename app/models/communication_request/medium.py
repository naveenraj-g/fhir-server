from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class CommunicationRequestMedium(TenantAuditMixin, Base):
    """CommunicationRequest.medium (0..*) child table."""

    __tablename__ = "communication_request_medium"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    communication_request_pk = Column(
        BigInteger,
        ForeignKey("communication_request.id"),
        nullable=False,
        index=True,
    )

    text = Column(String, nullable=True)

    communication_request = relationship(
        "CommunicationRequestModel", back_populates="medium_list"
    )
    codings = relationship(
        "CommunicationRequestMediumCoding",
        back_populates="medium",
        cascade="all, delete-orphan",
    )


class CommunicationRequestMediumCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """CommunicationRequest.medium.coding (0..*) grandchild table."""

    __tablename__ = "communication_request_medium_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    communication_request_medium_id = Column(
        BigInteger,
        ForeignKey("communication_request_medium.id"),
        nullable=False,
        index=True,
    )

    medium = relationship(
        "CommunicationRequestMedium", back_populates="codings"
    )
