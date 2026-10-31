from sqlalchemy import BigInteger, Column, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirAddressMixin, TenantAuditMixin


class RelatedPersonAddress(FhirAddressMixin, TenantAuditMixin, Base):
    """RelatedPerson.address (0..*) Address child table."""

    __tablename__ = "related_person_address"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    related_person_pk = Column(
        BigInteger, ForeignKey("related_person.id"), nullable=False, index=True
    )

    related_person = relationship("RelatedPersonModel", back_populates="addresses")
