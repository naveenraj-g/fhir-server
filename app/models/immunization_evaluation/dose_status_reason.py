from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin
from app.models.shared.datatypes import FhirCodingMixin


class ImmunizationEvaluationDoseStatusReasonModel(TenantAuditMixin, Base):
    """ImmunizationEvaluation.doseStatusReason (0..* CodeableConcept) child table."""

    __tablename__ = "immunization_evaluation_dose_status_reason"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    immunization_evaluation_pk = Column(
        BigInteger,
        ForeignKey("immunization_evaluation.id"),
        nullable=False,
        index=True,
    )

    text = Column(String, nullable=True)

    immunization_evaluation = relationship(
        "ImmunizationEvaluationModel", back_populates="dose_status_reasons"
    )
    codings = relationship(
        "ImmunizationEvaluationDoseStatusReasonCodingModel",
        back_populates="dose_status_reason",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class ImmunizationEvaluationDoseStatusReasonCodingModel(
    FhirCodingMixin, TenantAuditMixin, Base
):
    """ImmunizationEvaluation.doseStatusReason.coding (0..* Coding) grandchild table."""

    __tablename__ = "immunization_evaluation_dose_status_reason_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    dose_status_reason_id = Column(
        BigInteger,
        ForeignKey("immunization_evaluation_dose_status_reason.id"),
        nullable=False,
        index=True,
    )

    dose_status_reason = relationship(
        "ImmunizationEvaluationDoseStatusReasonModel", back_populates="codings"
    )
