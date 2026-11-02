from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin
from app.models.shared.datatypes import FhirCodingMixin


class ImmunizationSubpotentReasonModel(TenantAuditMixin, Base):
    """Immunization.subpotentReason (0..* CodeableConcept) child table."""

    __tablename__ = "immunization_subpotent_reason"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    immunization_pk = Column(
        BigInteger, ForeignKey("immunization.id"), nullable=False, index=True
    )

    text = Column(String, nullable=True)

    immunization = relationship("ImmunizationModel", back_populates="subpotent_reasons")
    codings = relationship(
        "ImmunizationSubpotentReasonCodingModel",
        back_populates="subpotent_reason",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class ImmunizationSubpotentReasonCodingModel(FhirCodingMixin, TenantAuditMixin, Base):
    """Immunization.subpotentReason.coding (0..* Coding) grandchild table."""

    __tablename__ = "immunization_subpotent_reason_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    subpotent_reason_id = Column(
        BigInteger,
        ForeignKey("immunization_subpotent_reason.id"),
        nullable=False,
        index=True,
    )

    subpotent_reason = relationship(
        "ImmunizationSubpotentReasonModel", back_populates="codings"
    )
