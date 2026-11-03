from sqlalchemy import BigInteger, Column, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class MeasureGroup(TenantAuditMixin, Base):
    """Measure.group (0..* BackboneElement) child table."""

    __tablename__ = "measure_group"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    measure_pk = Column(
        BigInteger, ForeignKey("measure.id", ondelete="CASCADE"), nullable=False, index=True
    )
    code_text = Column(String, nullable=True)
    description = Column(String, nullable=True)

    measure = relationship("MeasureModel", back_populates="groups")
    code_codings = relationship(
        "MeasureGroupCodeCoding",
        back_populates="group",
        cascade="all, delete-orphan",
    )
    populations = relationship(
        "MeasureGroupPopulation",
        back_populates="group",
        cascade="all, delete-orphan",
    )
    stratifiers = relationship(
        "MeasureGroupStratifier",
        back_populates="group",
        cascade="all, delete-orphan",
    )


class MeasureGroupCodeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """Coding within Measure.group.code."""

    __tablename__ = "measure_group_code_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    measure_group_id = Column(
        BigInteger,
        ForeignKey("measure_group.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    group = relationship("MeasureGroup", back_populates="code_codings")


class MeasureGroupPopulation(TenantAuditMixin, Base):
    """Measure.group.population (0..* BackboneElement) child table."""

    __tablename__ = "measure_group_population"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    measure_group_id = Column(
        BigInteger,
        ForeignKey("measure_group.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    code_text = Column(String, nullable=True)
    description = Column(String, nullable=True)

    # criteria (1..1 Expression)
    criteria_description = Column(String, nullable=True)
    criteria_name = Column(String, nullable=True)
    criteria_language = Column(String, nullable=True)
    criteria_expression = Column(Text, nullable=True)
    criteria_reference = Column(String, nullable=True)

    group = relationship("MeasureGroup", back_populates="populations")
    code_codings = relationship(
        "MeasureGroupPopulationCodeCoding",
        back_populates="population",
        cascade="all, delete-orphan",
    )


class MeasureGroupPopulationCodeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """Coding within Measure.group.population.code."""

    __tablename__ = "measure_group_population_code_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    measure_group_population_id = Column(
        BigInteger,
        ForeignKey("measure_group_population.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    population = relationship("MeasureGroupPopulation", back_populates="code_codings")


class MeasureGroupStratifier(TenantAuditMixin, Base):
    """Measure.group.stratifier (0..* BackboneElement) child table."""

    __tablename__ = "measure_group_stratifier"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    measure_group_id = Column(
        BigInteger,
        ForeignKey("measure_group.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    code_text = Column(String, nullable=True)
    description = Column(String, nullable=True)

    # criteria (0..1 Expression)
    criteria_description = Column(String, nullable=True)
    criteria_name = Column(String, nullable=True)
    criteria_language = Column(String, nullable=True)
    criteria_expression = Column(Text, nullable=True)
    criteria_reference = Column(String, nullable=True)

    group = relationship("MeasureGroup", back_populates="stratifiers")
    code_codings = relationship(
        "MeasureGroupStratifierCodeCoding",
        back_populates="stratifier",
        cascade="all, delete-orphan",
    )
    components = relationship(
        "MeasureGroupStratifierComponent",
        back_populates="stratifier",
        cascade="all, delete-orphan",
    )


class MeasureGroupStratifierCodeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """Coding within Measure.group.stratifier.code."""

    __tablename__ = "measure_group_stratifier_code_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    measure_group_stratifier_id = Column(
        BigInteger,
        ForeignKey("measure_group_stratifier.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    stratifier = relationship("MeasureGroupStratifier", back_populates="code_codings")


class MeasureGroupStratifierComponent(TenantAuditMixin, Base):
    """Measure.group.stratifier.component (0..* BackboneElement) child table."""

    __tablename__ = "measure_group_stratifier_component"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    measure_group_stratifier_id = Column(
        BigInteger,
        ForeignKey("measure_group_stratifier.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    code_text = Column(String, nullable=True)
    description = Column(String, nullable=True)

    # criteria (1..1 Expression)
    criteria_description = Column(String, nullable=True)
    criteria_name = Column(String, nullable=True)
    criteria_language = Column(String, nullable=True)
    criteria_expression = Column(Text, nullable=True)
    criteria_reference = Column(String, nullable=True)

    stratifier = relationship("MeasureGroupStratifier", back_populates="components")
    code_codings = relationship(
        "MeasureGroupStratifierComponentCodeCoding",
        back_populates="component",
        cascade="all, delete-orphan",
    )


class MeasureGroupStratifierComponentCodeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """Coding within Measure.group.stratifier.component.code."""

    __tablename__ = "measure_group_stratifier_component_code_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    measure_group_stratifier_component_id = Column(
        BigInteger,
        ForeignKey("measure_group_stratifier_component.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    component = relationship("MeasureGroupStratifierComponent", back_populates="code_codings")
