from sqlalchemy import BigInteger, Column, Enum, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.goal.enums import GoalOutcomeReferenceType
from app.models.shared import TenantAuditMixin


class GoalAddresses(TenantAuditMixin, Base):
    """Goal.addresses (0..*) child table.
    Reference(Condition|Observation|MedicationStatement|NutritionOrder|ServiceRequest|RiskAssessment).
    No UniqueConstraint on references per FHIR R4 rules.
    """

    __tablename__ = "goal_addresses"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    goal_pk = Column(
        BigInteger, ForeignKey("goal.id"), nullable=False, index=True
    )

    reference_reference = Column(String, nullable=True)
    reference_type = Column(String, nullable=True)
    reference_id = Column(BigInteger, nullable=True, index=True)
    reference_display = Column(String, nullable=True)

    goal = relationship("GoalModel", back_populates="addresses_list")


class GoalOutcomeReference(TenantAuditMixin, Base):
    """Goal.outcomeReference (0..*) child table. Reference(Observation)."""

    __tablename__ = "goal_outcome_reference"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    goal_pk = Column(
        BigInteger, ForeignKey("goal.id"), nullable=False, index=True
    )

    reference_reference = Column(String, nullable=True)
    reference_type = Column(
        Enum(GoalOutcomeReferenceType, name="goal_outcome_reference_type"),
        nullable=True,
    )
    reference_id = Column(BigInteger, nullable=True, index=True)
    reference_display = Column(String, nullable=True)

    goal = relationship("GoalModel", back_populates="outcome_references")
