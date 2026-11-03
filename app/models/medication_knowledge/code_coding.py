from sqlalchemy import BigInteger, Column, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class MedicationKnowledgeCodeCoding(Base, TenantAuditMixin, FhirCodingMixin):
    """MedicationKnowledge.code.coding (0..* Coding) child table."""

    __tablename__ = "medication_knowledge_code_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_knowledge_pk = Column(
        BigInteger,
        ForeignKey("medication_knowledge.id"),
        nullable=False,
        index=True,
    )

    medication_knowledge = relationship(
        "MedicationKnowledgeModel", back_populates="code_codings"
    )
