from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin
from app.models.shared.datatypes import FhirCodingMixin


class ImmunizationReasonCodeModel(TenantAuditMixin, Base):
    """Immunization.reasonCode (0..* CodeableConcept) child table."""

    __tablename__ = "immunization_reason_code"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    immunization_pk = Column(
        BigInteger, ForeignKey("immunization.id"), nullable=False, index=True
    )

    text = Column(String, nullable=True)

    immunization = relationship("ImmunizationModel", back_populates="reason_codes")
    codings = relationship(
        "ImmunizationReasonCodeCodingModel",
        back_populates="reason_code",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class ImmunizationReasonCodeCodingModel(FhirCodingMixin, TenantAuditMixin, Base):
    """Immunization.reasonCode.coding (0..* Coding) grandchild table."""

    __tablename__ = "immunization_reason_code_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    reason_code_id = Column(
        BigInteger, ForeignKey("immunization_reason_code.id"), nullable=False, index=True
    )

    reason_code = relationship("ImmunizationReasonCodeModel", back_populates="codings")
