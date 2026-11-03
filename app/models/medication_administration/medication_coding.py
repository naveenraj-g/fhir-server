from sqlalchemy import BigInteger, Column, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class MedicationAdministrationMedicationCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """MedicationAdministration.medicationCodeableConcept.coding (0..*) child table."""

    __tablename__ = "medication_administration_medication_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_administration_pk = Column(
        BigInteger, ForeignKey("medication_administration.id"), nullable=False, index=True
    )

    medication_administration = relationship(
        "MedicationAdministrationModel", back_populates="medication_codings"
    )
