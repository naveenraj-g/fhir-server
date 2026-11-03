from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class MedicationAdministrationStatusReason(TenantAuditMixin, Base):
    """MedicationAdministration.statusReason (0..* CodeableConcept) child table."""

    __tablename__ = "medication_administration_status_reason"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_administration_pk = Column(
        BigInteger, ForeignKey("medication_administration.id"), nullable=False, index=True
    )

    text = Column(String, nullable=True)

    medication_administration = relationship(
        "MedicationAdministrationModel", back_populates="status_reasons"
    )
    codings = relationship(
        "MedicationAdministrationStatusReasonCoding",
        back_populates="status_reason",
        cascade="all, delete-orphan",
    )


class MedicationAdministrationStatusReasonCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """MedicationAdministration.statusReason.coding (0..*) grandchild table."""

    __tablename__ = "medication_administration_status_reason_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_administration_status_reason_id = Column(
        BigInteger,
        ForeignKey("medication_administration_status_reason.id"),
        nullable=False,
        index=True,
    )

    status_reason = relationship(
        "MedicationAdministrationStatusReason", back_populates="codings"
    )
