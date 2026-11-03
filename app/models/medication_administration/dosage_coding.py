from sqlalchemy import BigInteger, Column, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class MedicationAdministrationDosageSiteCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """MedicationAdministration.dosage.site.coding (0..*) child table."""

    __tablename__ = "medication_administration_dosage_site_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_administration_pk = Column(
        BigInteger, ForeignKey("medication_administration.id"), nullable=False, index=True
    )

    medication_administration = relationship(
        "MedicationAdministrationModel", back_populates="dosage_site_codings"
    )


class MedicationAdministrationDosageRouteCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """MedicationAdministration.dosage.route.coding (0..*) child table."""

    __tablename__ = "medication_administration_dosage_route_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_administration_pk = Column(
        BigInteger, ForeignKey("medication_administration.id"), nullable=False, index=True
    )

    medication_administration = relationship(
        "MedicationAdministrationModel", back_populates="dosage_route_codings"
    )


class MedicationAdministrationDosageMethodCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """MedicationAdministration.dosage.method.coding (0..*) child table."""

    __tablename__ = "medication_administration_dosage_method_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_administration_pk = Column(
        BigInteger, ForeignKey("medication_administration.id"), nullable=False, index=True
    )

    medication_administration = relationship(
        "MedicationAdministrationModel", back_populates="dosage_method_codings"
    )
