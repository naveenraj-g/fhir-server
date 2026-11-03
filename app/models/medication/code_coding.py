from sqlalchemy import BigInteger, Column, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class MedicationCodeCoding(Base, TenantAuditMixin, FhirCodingMixin):
    """Medication.code.coding (0..* Coding) child table."""

    __tablename__ = "medication_code_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_pk = Column(
        BigInteger,
        ForeignKey("medication.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    medication = relationship("MedicationModel", back_populates="code_codings")
