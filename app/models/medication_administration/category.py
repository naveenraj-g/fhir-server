from sqlalchemy import BigInteger, Column, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class MedicationAdministrationCategoryCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """MedicationAdministration.category.coding (0..*) child table."""

    __tablename__ = "medication_administration_category_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_administration_pk = Column(
        BigInteger, ForeignKey("medication_administration.id"), nullable=False, index=True
    )

    medication_administration = relationship(
        "MedicationAdministrationModel", back_populates="category_codings"
    )
