from sqlalchemy import BigInteger, Column, Enum, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.care_plan.enums import (
    CarePlanAddressesReferenceType,
    CarePlanBasedOnReferenceType,
    CarePlanCareTeamReferenceType,
    CarePlanContributorReferenceType,
    CarePlanGoalReferenceType,
    CarePlanPartOfReferenceType,
    CarePlanReplacesReferenceType,
)
from app.models.shared import TenantAuditMixin


class CarePlanBasedOn(TenantAuditMixin, Base):
    """CarePlan.basedOn (0..*) child table."""

    __tablename__ = "care_plan_based_on"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    care_plan_pk = Column(
        BigInteger, ForeignKey("care_plan.id"), nullable=False, index=True
    )

    reference_reference = Column(String, nullable=True)
    reference_type = Column(
        Enum(
            CarePlanBasedOnReferenceType,
            name="care_plan_based_on_reference_type",
        ),
        nullable=True,
    )
    reference_id = Column(BigInteger, nullable=True, index=True)
    reference_display = Column(String, nullable=True)

    care_plan = relationship("CarePlanModel", back_populates="based_on")


class CarePlanReplaces(TenantAuditMixin, Base):
    """CarePlan.replaces (0..*) child table."""

    __tablename__ = "care_plan_replaces"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    care_plan_pk = Column(
        BigInteger, ForeignKey("care_plan.id"), nullable=False, index=True
    )

    reference_reference = Column(String, nullable=True)
    reference_type = Column(
        Enum(
            CarePlanReplacesReferenceType,
            name="care_plan_replaces_reference_type",
        ),
        nullable=True,
    )
    reference_id = Column(BigInteger, nullable=True, index=True)
    reference_display = Column(String, nullable=True)

    care_plan = relationship("CarePlanModel", back_populates="replaces")


class CarePlanPartOf(TenantAuditMixin, Base):
    """CarePlan.partOf (0..*) child table."""

    __tablename__ = "care_plan_part_of"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    care_plan_pk = Column(
        BigInteger, ForeignKey("care_plan.id"), nullable=False, index=True
    )

    reference_reference = Column(String, nullable=True)
    reference_type = Column(
        Enum(
            CarePlanPartOfReferenceType,
            name="care_plan_part_of_reference_type",
        ),
        nullable=True,
    )
    reference_id = Column(BigInteger, nullable=True, index=True)
    reference_display = Column(String, nullable=True)

    care_plan = relationship("CarePlanModel", back_populates="part_of")


class CarePlanContributor(TenantAuditMixin, Base):
    """CarePlan.contributor (0..*) child table."""

    __tablename__ = "care_plan_contributor"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    care_plan_pk = Column(
        BigInteger, ForeignKey("care_plan.id"), nullable=False, index=True
    )

    reference_reference = Column(String, nullable=True)
    reference_type = Column(
        Enum(
            CarePlanContributorReferenceType,
            name="care_plan_contributor_reference_type",
        ),
        nullable=True,
    )
    reference_id = Column(BigInteger, nullable=True, index=True)
    reference_display = Column(String, nullable=True)

    care_plan = relationship("CarePlanModel", back_populates="contributors")


class CarePlanCareTeam(TenantAuditMixin, Base):
    """CarePlan.careTeam (0..*) child table."""

    __tablename__ = "care_plan_care_team"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    care_plan_pk = Column(
        BigInteger, ForeignKey("care_plan.id"), nullable=False, index=True
    )

    reference_reference = Column(String, nullable=True)
    reference_type = Column(
        Enum(
            CarePlanCareTeamReferenceType,
            name="care_plan_care_team_reference_type",
        ),
        nullable=True,
    )
    reference_id = Column(BigInteger, nullable=True, index=True)
    reference_display = Column(String, nullable=True)

    care_plan = relationship("CarePlanModel", back_populates="care_teams")


class CarePlanAddresses(TenantAuditMixin, Base):
    """CarePlan.addresses (0..*) child table."""

    __tablename__ = "care_plan_addresses"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    care_plan_pk = Column(
        BigInteger, ForeignKey("care_plan.id"), nullable=False, index=True
    )

    reference_reference = Column(String, nullable=True)
    reference_type = Column(
        Enum(
            CarePlanAddressesReferenceType,
            name="care_plan_addresses_reference_type",
        ),
        nullable=True,
    )
    reference_id = Column(BigInteger, nullable=True, index=True)
    reference_display = Column(String, nullable=True)

    care_plan = relationship("CarePlanModel", back_populates="addresses")


class CarePlanGoal(TenantAuditMixin, Base):
    """CarePlan.goal (0..*) child table."""

    __tablename__ = "care_plan_goal"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    care_plan_pk = Column(
        BigInteger, ForeignKey("care_plan.id"), nullable=False, index=True
    )

    reference_reference = Column(String, nullable=True)
    reference_type = Column(
        Enum(
            CarePlanGoalReferenceType,
            name="care_plan_goal_reference_type",
        ),
        nullable=True,
    )
    reference_id = Column(BigInteger, nullable=True, index=True)
    reference_display = Column(String, nullable=True)

    care_plan = relationship("CarePlanModel", back_populates="goals")
