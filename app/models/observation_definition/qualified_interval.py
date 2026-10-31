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
from app.models.observation_definition.enums import (
    ObservationDefinitionGender,
    ObservationDefinitionQualifiedIntervalCategory,
)
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class ObservationDefinitionQualifiedInterval(TenantAuditMixin, Base):
    """ObservationDefinition.qualifiedInterval (0..*) child table."""

    __tablename__ = "observation_definition_qualified_interval"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    observation_definition_pk = Column(
        BigInteger, ForeignKey("observation_definition.id"), nullable=False, index=True
    )

    category = Column(
        Enum(
            ObservationDefinitionQualifiedIntervalCategory,
            name="observation_definition_qualified_interval_category",
        ),
        nullable=True,
    )

    # range (0..1 Range)
    range_low_value = Column(Numeric, nullable=True)
    range_low_unit = Column(String, nullable=True)
    range_low_system = Column(String, nullable=True)
    range_low_code = Column(String, nullable=True)
    range_high_value = Column(Numeric, nullable=True)
    range_high_unit = Column(String, nullable=True)
    range_high_system = Column(String, nullable=True)
    range_high_code = Column(String, nullable=True)

    # context (0..1 CodeableConcept)
    context_text = Column(String, nullable=True)

    # gender (0..1 code)
    gender = Column(
        Enum(
            ObservationDefinitionGender,
            name="observation_definition_gender",
        ),
        nullable=True,
    )

    # age (0..1 Range)
    age_low_value = Column(Numeric, nullable=True)
    age_low_unit = Column(String, nullable=True)
    age_low_system = Column(String, nullable=True)
    age_low_code = Column(String, nullable=True)
    age_high_value = Column(Numeric, nullable=True)
    age_high_unit = Column(String, nullable=True)
    age_high_system = Column(String, nullable=True)
    age_high_code = Column(String, nullable=True)

    # gestationalAge (0..1 Range)
    gestational_age_low_value = Column(Numeric, nullable=True)
    gestational_age_low_unit = Column(String, nullable=True)
    gestational_age_low_system = Column(String, nullable=True)
    gestational_age_low_code = Column(String, nullable=True)
    gestational_age_high_value = Column(Numeric, nullable=True)
    gestational_age_high_unit = Column(String, nullable=True)
    gestational_age_high_system = Column(String, nullable=True)
    gestational_age_high_code = Column(String, nullable=True)

    # condition (0..1 string)
    condition = Column(String, nullable=True)

    observation_definition = relationship(
        "ObservationDefinitionModel", back_populates="qualified_intervals"
    )
    context_codings = relationship(
        "ObservationDefinitionQualifiedIntervalContextCoding",
        back_populates="qualified_interval",
        cascade="all, delete-orphan",
    )
    applies_tos = relationship(
        "ObservationDefinitionQualifiedIntervalAppliesTo",
        back_populates="qualified_interval",
        cascade="all, delete-orphan",
    )


class ObservationDefinitionQualifiedIntervalContextCoding(
    FhirCodingMixin, TenantAuditMixin, Base
):
    """ObservationDefinition.qualifiedInterval.context.coding (0..*) child table."""

    __tablename__ = "observation_definition_qualified_interval_context_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    qualified_interval_id = Column(
        BigInteger,
        ForeignKey("observation_definition_qualified_interval.id"),
        nullable=False,
        index=True,
    )

    qualified_interval = relationship(
        "ObservationDefinitionQualifiedInterval", back_populates="context_codings"
    )


class ObservationDefinitionQualifiedIntervalAppliesTo(TenantAuditMixin, Base):
    """ObservationDefinition.qualifiedInterval.appliesTo (0..* CodeableConcept) child table."""

    __tablename__ = "observation_definition_qualified_interval_applies_to"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    qualified_interval_id = Column(
        BigInteger,
        ForeignKey("observation_definition_qualified_interval.id"),
        nullable=False,
        index=True,
    )
    text = Column(String, nullable=True)

    qualified_interval = relationship(
        "ObservationDefinitionQualifiedInterval", back_populates="applies_tos"
    )
    codings = relationship(
        "ObservationDefinitionQualifiedIntervalAppliesToCoding",
        back_populates="applies_to",
        cascade="all, delete-orphan",
    )


class ObservationDefinitionQualifiedIntervalAppliesToCoding(
    FhirCodingMixin, TenantAuditMixin, Base
):
    """ObservationDefinition.qualifiedInterval.appliesTo.coding (0..*) grandchild table."""

    __tablename__ = "observation_definition_qualified_interval_applies_to_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    applies_to_id = Column(
        BigInteger,
        ForeignKey("observation_definition_qualified_interval_applies_to.id"),
        nullable=False,
        index=True,
    )

    applies_to = relationship(
        "ObservationDefinitionQualifiedIntervalAppliesTo", back_populates="codings"
    )
