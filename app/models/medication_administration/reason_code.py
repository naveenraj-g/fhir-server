from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class MedicationAdministrationReasonCode(TenantAuditMixin, Base):
    """MedicationAdministration.reasonCode (0..* CodeableConcept) child table."""

    __tablename__ = "medication_administration_reason_code"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_administration_pk = Column(
        BigInteger, ForeignKey("medication_administration.id"), nullable=False, index=True
    )

    text = Column(String, nullable=True)

    medication_administration = relationship(
        "MedicationAdministrationModel", back_populates="reason_codes"
    )
    codings = relationship(
        "MedicationAdministrationReasonCodeCoding",
        back_populates="reason_code",
        cascade="all, delete-orphan",
    )


class MedicationAdministrationReasonCodeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """MedicationAdministration.reasonCode.coding (0..*) grandchild table."""

    __tablename__ = "medication_administration_reason_code_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_administration_reason_code_id = Column(
        BigInteger,
        ForeignKey("medication_administration_reason_code.id"),
        nullable=False,
        index=True,
    )

    reason_code = relationship(
        "MedicationAdministrationReasonCode", back_populates="codings"
    )
