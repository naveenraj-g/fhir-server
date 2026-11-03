from sqlalchemy import BigInteger, Column, ForeignKey, Numeric, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class MedicationKnowledgeCost(Base, TenantAuditMixin):
    """MedicationKnowledge.cost (0..* BackboneElement)."""

    __tablename__ = "medication_knowledge_cost"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_knowledge_pk = Column(
        BigInteger,
        ForeignKey("medication_knowledge.id"),
        nullable=False,
        index=True,
    )

    type_text = Column(String, nullable=True)
    source = Column(String, nullable=True)

    # cost (1..1 Money)
    cost_value = Column(Numeric, nullable=True)
    cost_currency = Column(String, nullable=True)

    medication_knowledge = relationship(
        "MedicationKnowledgeModel", back_populates="costs"
    )
    type_codings = relationship(
        "MedicationKnowledgeCostTypeCoding",
        back_populates="cost",
        cascade="all, delete-orphan",
    )


class MedicationKnowledgeCostTypeCoding(Base, TenantAuditMixin, FhirCodingMixin):
    """MedicationKnowledge.cost.type.coding (0..* Coding)."""

    __tablename__ = "medication_knowledge_cost_type_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_knowledge_cost_id = Column(
        BigInteger,
        ForeignKey("medication_knowledge_cost.id"),
        nullable=False,
        index=True,
    )

    cost = relationship("MedicationKnowledgeCost", back_populates="type_codings")
