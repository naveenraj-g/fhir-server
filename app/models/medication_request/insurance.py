from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    String,
)
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.enums import IdentifierUse
from app.models.medication_request.enums import MedicationRequestInsuranceReferenceType
from app.models.shared import TenantAuditMixin


class MedicationRequestInsurance(TenantAuditMixin, Base):
    """insurance[] — neither Coverage nor ClaimResponse is a modeled
    resource in this system.

    No UniqueConstraint on (medication_request_pk, reference_type,
    reference_id): R4 doesn't forbid listing the same reference twice — a
    deployment that wants that as a rule expresses it as a profile-layer
    invariant, not a base constraint."""

    __tablename__ = "medication_request_insurance"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_request_pk = Column(BigInteger, ForeignKey("medication_request.id"), nullable=False, index=True)

    reference_reference = Column(String, nullable=True)
    reference_type = Column(
        Enum(MedicationRequestInsuranceReferenceType, name="medication_request_insurance_reference_type"), nullable=True
    )
    reference_id = Column(BigInteger, nullable=True, index=True)
    reference_display = Column(String, nullable=True)

    reference_identifier_use = Column(Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True)
    reference_identifier_type_system = Column(String, nullable=True)
    reference_identifier_type_version = Column(String, nullable=True)
    reference_identifier_type_code = Column(String, nullable=True)
    reference_identifier_type_display = Column(String, nullable=True)
    reference_identifier_type_text = Column(String, nullable=True)
    reference_identifier_type_user_selected = Column(Boolean, nullable=True)
    reference_identifier_system = Column(String, nullable=True)
    reference_identifier_value = Column(String, nullable=True)
    reference_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    reference_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    medication_request = relationship("MedicationRequestModel", back_populates="insurances")
