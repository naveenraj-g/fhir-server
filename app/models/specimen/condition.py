from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class SpecimenCondition(TenantAuditMixin, Base):
    """One entry of Specimen.condition (0..* CodeableConcept)."""

    __tablename__ = "specimen_condition"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    specimen_pk = Column(
        BigInteger, ForeignKey("specimen.id"), nullable=False, index=True
    )

    text = Column(String, nullable=True)

    specimen = relationship("SpecimenModel", back_populates="conditions")
    codings = relationship(
        "SpecimenConditionCoding",
        back_populates="condition",
        cascade="all, delete-orphan",
    )


class SpecimenConditionCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Specimen.condition.coding (0..*)."""

    __tablename__ = "specimen_condition_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    specimen_condition_id = Column(
        BigInteger,
        ForeignKey("specimen_condition.id"),
        nullable=False,
        index=True,
    )

    condition = relationship("SpecimenCondition", back_populates="codings")
