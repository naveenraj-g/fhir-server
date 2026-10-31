from sqlalchemy import BigInteger, Column, Enum, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.activity_definition.enums import (
    ActivityDefinitionObservationRequirementReferenceType,
    ActivityDefinitionObservationResultRequirementReferenceType,
    ActivityDefinitionSpecimenRequirementReferenceType,
)
from app.models.shared import TenantAuditMixin


class ActivityDefinitionSpecimenRequirement(TenantAuditMixin, Base):
    """ActivityDefinition.specimenRequirement (0..* Reference(SpecimenDefinition)) child table."""

    __tablename__ = "activity_definition_specimen_requirement"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    activity_definition_pk = Column(
        BigInteger, ForeignKey("activity_definition.id", ondelete="CASCADE"), nullable=False, index=True
    )

    reference_reference = Column(String, nullable=True)
    reference_type = Column(
        Enum(
            ActivityDefinitionSpecimenRequirementReferenceType,
            name="activity_definition_specimen_req_reference_type",
        ),
        nullable=True,
    )
    reference_id = Column(BigInteger, nullable=True, index=True)
    reference_display = Column(String, nullable=True)

    activity_definition = relationship(
        "ActivityDefinitionModel", back_populates="specimen_requirements"
    )


class ActivityDefinitionObservationRequirement(TenantAuditMixin, Base):
    """ActivityDefinition.observationRequirement (0..* Reference(ObservationDefinition)) child table."""

    __tablename__ = "activity_definition_observation_requirement"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    activity_definition_pk = Column(
        BigInteger, ForeignKey("activity_definition.id", ondelete="CASCADE"), nullable=False, index=True
    )

    reference_reference = Column(String, nullable=True)
    reference_type = Column(
        Enum(
            ActivityDefinitionObservationRequirementReferenceType,
            name="activity_definition_observation_req_reference_type",
        ),
        nullable=True,
    )
    reference_id = Column(BigInteger, nullable=True, index=True)
    reference_display = Column(String, nullable=True)

    activity_definition = relationship(
        "ActivityDefinitionModel", back_populates="observation_requirements"
    )


class ActivityDefinitionObservationResultRequirement(TenantAuditMixin, Base):
    """ActivityDefinition.observationResultRequirement (0..* Reference(ObservationDefinition)) child table."""

    __tablename__ = "activity_definition_observation_result_requirement"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    activity_definition_pk = Column(
        BigInteger, ForeignKey("activity_definition.id", ondelete="CASCADE"), nullable=False, index=True
    )

    reference_reference = Column(String, nullable=True)
    reference_type = Column(
        Enum(
            ActivityDefinitionObservationResultRequirementReferenceType,
            name="activity_definition_observation_result_req_ref_type",
        ),
        nullable=True,
    )
    reference_id = Column(BigInteger, nullable=True, index=True)
    reference_display = Column(String, nullable=True)

    activity_definition = relationship(
        "ActivityDefinitionModel", back_populates="observation_result_requirements"
    )
