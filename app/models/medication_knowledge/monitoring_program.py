from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class MedicationKnowledgeMonitoringProgram(Base, TenantAuditMixin):
    """MedicationKnowledge.monitoringProgram (0..* BackboneElement)."""

    __tablename__ = "medication_knowledge_monitoring_program"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_knowledge_pk = Column(
        BigInteger,
        ForeignKey("medication_knowledge.id"),
        nullable=False,
        index=True,
    )

    type_text = Column(String, nullable=True)
    name = Column(String, nullable=True)

    medication_knowledge = relationship(
        "MedicationKnowledgeModel", back_populates="monitoring_programs"
    )
    type_codings = relationship(
        "MedicationKnowledgeMonitoringProgramTypeCoding",
        back_populates="monitoring_program",
        cascade="all, delete-orphan",
    )


class MedicationKnowledgeMonitoringProgramTypeCoding(Base, TenantAuditMixin, FhirCodingMixin):
    """MedicationKnowledge.monitoringProgram.type.coding (0..* Coding)."""

    __tablename__ = "medication_knowledge_monitoring_program_type_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_knowledge_monitoring_program_id = Column(
        BigInteger,
        ForeignKey("medication_knowledge_monitoring_program.id"),
        nullable=False,
        index=True,
    )

    monitoring_program = relationship(
        "MedicationKnowledgeMonitoringProgram", back_populates="type_codings"
    )
