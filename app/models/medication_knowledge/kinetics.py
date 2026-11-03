from sqlalchemy import (
    BigInteger,
    Column,
    Enum,
    ForeignKey,
    Numeric,
    String,
)
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.medication_knowledge.enums import (
    MedicationKnowledgeQuantityComparator,
)
from app.models.shared import TenantAuditMixin


class MedicationKnowledgeKinetics(Base, TenantAuditMixin):
    """MedicationKnowledge.kinetics (0..* BackboneElement)."""

    __tablename__ = "medication_knowledge_kinetics"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_knowledge_pk = Column(
        BigInteger,
        ForeignKey("medication_knowledge.id"),
        nullable=False,
        index=True,
    )

    # halfLifePeriod (0..1 Duration)
    half_life_period_value = Column(Numeric, nullable=True)
    half_life_period_comparator = Column(
        Enum(
            MedicationKnowledgeQuantityComparator,
            name="medication_knowledge_quantity_comparator",
            create_type=False,
        ),
        nullable=True,
    )
    half_life_period_unit = Column(String, nullable=True)
    half_life_period_system = Column(String, nullable=True)
    half_life_period_code = Column(String, nullable=True)

    medication_knowledge = relationship(
        "MedicationKnowledgeModel", back_populates="kinetics"
    )
    area_under_curve = relationship(
        "MedicationKnowledgeKineticsAreaUnderCurve",
        back_populates="kinetics",
        cascade="all, delete-orphan",
    )
    lethal_dose_50 = relationship(
        "MedicationKnowledgeKineticsLethalDose50",
        back_populates="kinetics",
        cascade="all, delete-orphan",
    )


class MedicationKnowledgeKineticsAreaUnderCurve(Base, TenantAuditMixin):
    """MedicationKnowledge.kinetics.areaUnderCurve (0..* SimpleQuantity)."""

    __tablename__ = "medication_knowledge_kinetics_auc"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_knowledge_kinetics_id = Column(
        BigInteger,
        ForeignKey("medication_knowledge_kinetics.id"),
        nullable=False,
        index=True,
    )

    value = Column(Numeric, nullable=True)
    comparator = Column(
        Enum(
            MedicationKnowledgeQuantityComparator,
            name="medication_knowledge_quantity_comparator",
            create_type=False,
        ),
        nullable=True,
    )
    unit = Column(String, nullable=True)
    system = Column(String, nullable=True)
    code = Column(String, nullable=True)

    kinetics = relationship(
        "MedicationKnowledgeKinetics", back_populates="area_under_curve"
    )


class MedicationKnowledgeKineticsLethalDose50(Base, TenantAuditMixin):
    """MedicationKnowledge.kinetics.lethalDose50 (0..* SimpleQuantity)."""

    __tablename__ = "medication_knowledge_kinetics_ld50"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_knowledge_kinetics_id = Column(
        BigInteger,
        ForeignKey("medication_knowledge_kinetics.id"),
        nullable=False,
        index=True,
    )

    value = Column(Numeric, nullable=True)
    comparator = Column(
        Enum(
            MedicationKnowledgeQuantityComparator,
            name="medication_knowledge_quantity_comparator",
            create_type=False,
        ),
        nullable=True,
    )
    unit = Column(String, nullable=True)
    system = Column(String, nullable=True)
    code = Column(String, nullable=True)

    kinetics = relationship(
        "MedicationKnowledgeKinetics", back_populates="lethal_dose_50"
    )
