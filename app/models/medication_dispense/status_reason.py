from sqlalchemy import BigInteger, Column, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class MedicationDispenseStatusReasonCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """MedicationDispense.statusReason.coding (0..*) child table."""

    __tablename__ = "medication_dispense_status_reason_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_dispense_pk = Column(
        BigInteger, ForeignKey("medication_dispense.id"), nullable=False, index=True
    )

    medication_dispense = relationship(
        "MedicationDispenseModel", back_populates="status_reason_codings"
    )
