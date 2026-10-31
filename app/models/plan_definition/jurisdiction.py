from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class PlanDefinitionJurisdiction(TenantAuditMixin, Base):
    """PlanDefinition.jurisdiction (0..* CodeableConcept) child table."""

    __tablename__ = "plan_definition_jurisdiction"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    plan_definition_pk = Column(
        BigInteger, ForeignKey("plan_definition.id", ondelete="CASCADE"), nullable=False, index=True
    )
    text = Column(String, nullable=True)

    plan_definition = relationship("PlanDefinitionModel", back_populates="jurisdictions")
    codings = relationship(
        "PlanDefinitionJurisdictionCoding",
        back_populates="jurisdiction",
        cascade="all, delete-orphan",
    )


class PlanDefinitionJurisdictionCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """PlanDefinition.jurisdiction.coding (0..* Coding) grandchild table."""

    __tablename__ = "plan_definition_jurisdiction_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    plan_definition_jurisdiction_id = Column(
        BigInteger,
        ForeignKey("plan_definition_jurisdiction.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    jurisdiction = relationship("PlanDefinitionJurisdiction", back_populates="codings")
