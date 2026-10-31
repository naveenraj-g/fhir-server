from sqlalchemy import BigInteger, Column, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class PlanDefinitionTypeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """PlanDefinition.type.coding (0..* Coding) child table."""

    __tablename__ = "plan_definition_type_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    plan_definition_pk = Column(
        BigInteger, ForeignKey("plan_definition.id", ondelete="CASCADE"), nullable=False, index=True
    )

    plan_definition = relationship("PlanDefinitionModel", back_populates="type_codings")


class PlanDefinitionSubjectCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """PlanDefinition.subjectCodeableConcept.coding (0..* Coding) child table."""

    __tablename__ = "plan_definition_subject_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    plan_definition_pk = Column(
        BigInteger, ForeignKey("plan_definition.id", ondelete="CASCADE"), nullable=False, index=True
    )

    plan_definition = relationship("PlanDefinitionModel", back_populates="subject_codings")
