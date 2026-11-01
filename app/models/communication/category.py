from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class CommunicationCategory(TenantAuditMixin, Base):
    """Communication.category (0..*) child table."""

    __tablename__ = "communication_category"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    communication_pk = Column(
        BigInteger,
        ForeignKey("communication.id"),
        nullable=False,
        index=True,
    )

    text = Column(String, nullable=True)

    communication = relationship(
        "CommunicationModel", back_populates="categories"
    )
    codings = relationship(
        "CommunicationCategoryCoding",
        back_populates="category",
        cascade="all, delete-orphan",
    )


class CommunicationCategoryCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """Communication.category.coding (0..*) grandchild table."""

    __tablename__ = "communication_category_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    communication_category_id = Column(
        BigInteger,
        ForeignKey("communication_category.id"),
        nullable=False,
        index=True,
    )

    category = relationship(
        "CommunicationCategory", back_populates="codings"
    )
