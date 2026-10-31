from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class CommunicationRequestCategory(TenantAuditMixin, Base):
    """CommunicationRequest.category (0..*) child table."""

    __tablename__ = "communication_request_category"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    communication_request_pk = Column(
        BigInteger,
        ForeignKey("communication_request.id"),
        nullable=False,
        index=True,
    )

    text = Column(String, nullable=True)

    communication_request = relationship(
        "CommunicationRequestModel", back_populates="categories"
    )
    codings = relationship(
        "CommunicationRequestCategoryCoding",
        back_populates="category",
        cascade="all, delete-orphan",
    )


class CommunicationRequestCategoryCoding(
    FhirCodingMixin, TenantAuditMixin, Base
):
    """CommunicationRequest.category.coding (0..*) grandchild table."""

    __tablename__ = "communication_request_category_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    communication_request_category_id = Column(
        BigInteger,
        ForeignKey("communication_request_category.id"),
        nullable=False,
        index=True,
    )

    category = relationship(
        "CommunicationRequestCategory", back_populates="codings"
    )
