from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class CommunicationMedium(TenantAuditMixin, Base):
    """Communication.medium (0..*) child table."""

    __tablename__ = "communication_medium"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    communication_pk = Column(
        BigInteger,
        ForeignKey("communication.id"),
        nullable=False,
        index=True,
    )

    text = Column(String, nullable=True)

    communication = relationship(
        "CommunicationModel", back_populates="medium_list"
    )
    codings = relationship(
        "CommunicationMediumCoding",
        back_populates="medium",
        cascade="all, delete-orphan",
    )


class CommunicationMediumCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """Communication.medium.coding (0..*) grandchild table."""

    __tablename__ = "communication_medium_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    communication_medium_id = Column(
        BigInteger,
        ForeignKey("communication_medium.id"),
        nullable=False,
        index=True,
    )

    medium = relationship(
        "CommunicationMedium", back_populates="codings"
    )
