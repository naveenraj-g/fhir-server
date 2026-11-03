from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class MedicationKnowledgeIntendedRoute(Base, TenantAuditMixin):
    """MedicationKnowledge.intendedRoute (0..* CodeableConcept)."""

    __tablename__ = "medication_knowledge_intended_route"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_knowledge_pk = Column(
        BigInteger,
        ForeignKey("medication_knowledge.id"),
        nullable=False,
        index=True,
    )

    text = Column(String, nullable=True)

    medication_knowledge = relationship(
        "MedicationKnowledgeModel", back_populates="intended_routes"
    )
    codings = relationship(
        "MedicationKnowledgeIntendedRouteCoding",
        back_populates="intended_route",
        cascade="all, delete-orphan",
    )


class MedicationKnowledgeIntendedRouteCoding(Base, TenantAuditMixin, FhirCodingMixin):
    """MedicationKnowledge.intendedRoute.coding (0..* Coding)."""

    __tablename__ = "medication_knowledge_intended_route_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_knowledge_intended_route_id = Column(
        BigInteger,
        ForeignKey("medication_knowledge_intended_route.id"),
        nullable=False,
        index=True,
    )

    intended_route = relationship(
        "MedicationKnowledgeIntendedRoute", back_populates="codings"
    )
