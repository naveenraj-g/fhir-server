from sqlalchemy import BigInteger, Column, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class MedicationFormCoding(Base, TenantAuditMixin, FhirCodingMixin):
    """Medication.form.coding (0..* Coding) child table."""

    __tablename__ = "medication_form_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_pk = Column(
        BigInteger,
        ForeignKey("medication.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    medication = relationship("MedicationModel", back_populates="form_codings")
