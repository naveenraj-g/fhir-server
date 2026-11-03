from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    String,
)
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.enums import IdentifierUse
from app.models.measure_report.enums import (
    MeasureReportQuantityComparator,
    MeasureReportSubjectResultsReferenceType,
)
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class MeasureReportGroup(TenantAuditMixin, Base):
    """MeasureReport.group (0..*) child table."""

    __tablename__ = "measure_report_group"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    measure_report_pk = Column(
        BigInteger, ForeignKey("measure_report.id", ondelete="CASCADE"), nullable=False, index=True
    )

    code_text = Column(String, nullable=True)

    # measureScore (0..1 Quantity)
    measure_score_value = Column(Numeric, nullable=True)
    measure_score_comparator = Column(
        Enum(
            MeasureReportQuantityComparator,
            name="measure_report_quantity_comparator",
        ),
        nullable=True,
    )
    measure_score_unit = Column(String, nullable=True)
    measure_score_system = Column(String, nullable=True)
    measure_score_code = Column(String, nullable=True)

    measure_report = relationship("MeasureReportModel", back_populates="groups")
    code_coding = relationship(
        "MeasureReportGroupCodeCoding",
        back_populates="group",
        cascade="all, delete-orphan",
    )
    populations = relationship(
        "MeasureReportGroupPopulation",
        back_populates="group",
        cascade="all, delete-orphan",
    )
    stratifiers = relationship(
        "MeasureReportGroupStratifier",
        back_populates="group",
        cascade="all, delete-orphan",
    )


class MeasureReportGroupCodeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """MeasureReport.group.code.coding child table."""

    __tablename__ = "measure_report_group_code_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    group_id = Column(
        BigInteger,
        ForeignKey("measure_report_group.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    group = relationship("MeasureReportGroup", back_populates="code_coding")


class MeasureReportGroupPopulation(TenantAuditMixin, Base):
    """MeasureReport.group.population (0..*) child table."""

    __tablename__ = "measure_report_group_population"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    group_id = Column(
        BigInteger,
        ForeignKey("measure_report_group.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    code_text = Column(String, nullable=True)
    count = Column(BigInteger, nullable=True)

    # subjectResults (0..1 Reference(List))
    subject_results_reference = Column(String, nullable=True)
    subject_results_type = Column(
        Enum(
            MeasureReportSubjectResultsReferenceType,
            name="measure_report_subject_results_reference_type",
        ),
        nullable=True,
    )
    subject_results_id = Column(BigInteger, nullable=True, index=True)
    subject_results_display = Column(String, nullable=True)

    # fallback identifier (11 columns)
    subject_results_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    subject_results_identifier_type_system = Column(String, nullable=True)
    subject_results_identifier_type_version = Column(String, nullable=True)
    subject_results_identifier_type_code = Column(String, nullable=True)
    subject_results_identifier_type_display = Column(String, nullable=True)
    subject_results_identifier_type_user_selected = Column(Boolean, nullable=True)
    subject_results_identifier_type_text = Column(String, nullable=True)
    subject_results_identifier_system = Column(String, nullable=True)
    subject_results_identifier_value = Column(String, nullable=True)
    subject_results_identifier_period_start = Column(
        DateTime(timezone=True), nullable=True
    )
    subject_results_identifier_period_end = Column(
        DateTime(timezone=True), nullable=True
    )

    group = relationship("MeasureReportGroup", back_populates="populations")
    code_coding = relationship(
        "MeasureReportGroupPopulationCodeCoding",
        back_populates="population",
        cascade="all, delete-orphan",
    )


class MeasureReportGroupPopulationCodeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """MeasureReport.group.population.code.coding child table."""

    __tablename__ = "measure_report_group_population_code_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    population_id = Column(
        BigInteger,
        ForeignKey("measure_report_group_population.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    population = relationship("MeasureReportGroupPopulation", back_populates="code_coding")


class MeasureReportGroupStratifier(TenantAuditMixin, Base):
    """MeasureReport.group.stratifier (0..*) child table."""

    __tablename__ = "measure_report_group_stratifier"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    group_id = Column(
        BigInteger,
        ForeignKey("measure_report_group.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    group = relationship("MeasureReportGroup", back_populates="stratifiers")
    codes = relationship(
        "MeasureReportGroupStratifierCode",
        back_populates="stratifier",
        cascade="all, delete-orphan",
    )
    strata = relationship(
        "MeasureReportGroupStratifierStratum",
        back_populates="stratifier",
        cascade="all, delete-orphan",
    )


class MeasureReportGroupStratifierCode(TenantAuditMixin, Base):
    """MeasureReport.group.stratifier.code (0..* CodeableConcept) child table."""

    __tablename__ = "measure_report_group_stratifier_code"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    stratifier_id = Column(
        BigInteger,
        ForeignKey("measure_report_group_stratifier.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    code_text = Column(String, nullable=True)

    stratifier = relationship("MeasureReportGroupStratifier", back_populates="codes")
    coding = relationship(
        "MeasureReportGroupStratifierCodeCoding",
        back_populates="stratifier_code",
        cascade="all, delete-orphan",
    )


class MeasureReportGroupStratifierCodeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """MeasureReport.group.stratifier.code.coding child table."""

    __tablename__ = "measure_report_group_stratifier_code_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    stratifier_code_id = Column(
        BigInteger,
        ForeignKey("measure_report_group_stratifier_code.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    stratifier_code = relationship(
        "MeasureReportGroupStratifierCode", back_populates="coding"
    )


class MeasureReportGroupStratifierStratum(TenantAuditMixin, Base):
    """MeasureReport.group.stratifier.stratum (0..*) child table."""

    __tablename__ = "measure_report_group_stratifier_stratum"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    stratifier_id = Column(
        BigInteger,
        ForeignKey("measure_report_group_stratifier.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    value_text = Column(String, nullable=True)

    # measureScore (0..1 Quantity)
    measure_score_value = Column(Numeric, nullable=True)
    measure_score_comparator = Column(
        Enum(
            MeasureReportQuantityComparator,
            name="measure_report_quantity_comparator",
            create_type=False,
        ),
        nullable=True,
    )
    measure_score_unit = Column(String, nullable=True)
    measure_score_system = Column(String, nullable=True)
    measure_score_code = Column(String, nullable=True)

    stratifier = relationship("MeasureReportGroupStratifier", back_populates="strata")
    value_coding = relationship(
        "MeasureReportGroupStratifierStratumValueCoding",
        back_populates="stratum",
        cascade="all, delete-orphan",
    )
    components = relationship(
        "MeasureReportGroupStratifierStratumComponent",
        back_populates="stratum",
        cascade="all, delete-orphan",
    )
    populations = relationship(
        "MeasureReportGroupStratifierStratumPopulation",
        back_populates="stratum",
        cascade="all, delete-orphan",
    )


class MeasureReportGroupStratifierStratumValueCoding(
    FhirCodingMixin, TenantAuditMixin, Base
):
    """MeasureReport.group.stratifier.stratum.value.coding child table."""

    __tablename__ = "measure_report_group_stratifier_stratum_value_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    stratum_id = Column(
        BigInteger,
        ForeignKey("measure_report_group_stratifier_stratum.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    stratum = relationship(
        "MeasureReportGroupStratifierStratum", back_populates="value_coding"
    )


class MeasureReportGroupStratifierStratumComponent(TenantAuditMixin, Base):
    """MeasureReport.group.stratifier.stratum.component (0..*) child table."""

    __tablename__ = "measure_report_group_stratifier_stratum_component"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    stratum_id = Column(
        BigInteger,
        ForeignKey("measure_report_group_stratifier_stratum.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    code_text = Column(String, nullable=True)
    value_text = Column(String, nullable=True)

    stratum = relationship(
        "MeasureReportGroupStratifierStratum", back_populates="components"
    )
    code_coding = relationship(
        "MeasureReportGroupStratifierStratumComponentCodeCoding",
        back_populates="component",
        cascade="all, delete-orphan",
    )
    value_coding = relationship(
        "MeasureReportGroupStratifierStratumComponentValueCoding",
        back_populates="component",
        cascade="all, delete-orphan",
    )


class MeasureReportGroupStratifierStratumComponentCodeCoding(
    FhirCodingMixin, TenantAuditMixin, Base
):
    """MeasureReport.group.stratifier.stratum.component.code.coding child table."""

    __tablename__ = "measure_report_group_stratifier_stratum_comp_code_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    component_id = Column(
        BigInteger,
        ForeignKey(
            "measure_report_group_stratifier_stratum_component.id", ondelete="CASCADE"
        ),
        nullable=False,
        index=True,
    )

    component = relationship(
        "MeasureReportGroupStratifierStratumComponent", back_populates="code_coding"
    )


class MeasureReportGroupStratifierStratumComponentValueCoding(
    FhirCodingMixin, TenantAuditMixin, Base
):
    """MeasureReport.group.stratifier.stratum.component.value.coding child table."""

    __tablename__ = "measure_report_group_stratifier_stratum_comp_value_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    component_id = Column(
        BigInteger,
        ForeignKey(
            "measure_report_group_stratifier_stratum_component.id", ondelete="CASCADE"
        ),
        nullable=False,
        index=True,
    )

    component = relationship(
        "MeasureReportGroupStratifierStratumComponent", back_populates="value_coding"
    )


class MeasureReportGroupStratifierStratumPopulation(TenantAuditMixin, Base):
    """MeasureReport.group.stratifier.stratum.population (0..*) child table."""

    __tablename__ = "measure_report_group_stratifier_stratum_population"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    stratum_id = Column(
        BigInteger,
        ForeignKey("measure_report_group_stratifier_stratum.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    code_text = Column(String, nullable=True)
    count = Column(BigInteger, nullable=True)

    # subjectResults (0..1 Reference(List))
    subject_results_reference = Column(String, nullable=True)
    subject_results_type = Column(
        Enum(
            MeasureReportSubjectResultsReferenceType,
            name="measure_report_subject_results_reference_type",
            create_type=False,
        ),
        nullable=True,
    )
    subject_results_id = Column(BigInteger, nullable=True, index=True)
    subject_results_display = Column(String, nullable=True)

    # fallback identifier (11 columns)
    subject_results_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    subject_results_identifier_type_system = Column(String, nullable=True)
    subject_results_identifier_type_version = Column(String, nullable=True)
    subject_results_identifier_type_code = Column(String, nullable=True)
    subject_results_identifier_type_display = Column(String, nullable=True)
    subject_results_identifier_type_user_selected = Column(Boolean, nullable=True)
    subject_results_identifier_type_text = Column(String, nullable=True)
    subject_results_identifier_system = Column(String, nullable=True)
    subject_results_identifier_value = Column(String, nullable=True)
    subject_results_identifier_period_start = Column(
        DateTime(timezone=True), nullable=True
    )
    subject_results_identifier_period_end = Column(
        DateTime(timezone=True), nullable=True
    )

    stratum = relationship(
        "MeasureReportGroupStratifierStratum", back_populates="populations"
    )
    code_coding = relationship(
        "MeasureReportGroupStratifierStratumPopulationCodeCoding",
        back_populates="population",
        cascade="all, delete-orphan",
    )


class MeasureReportGroupStratifierStratumPopulationCodeCoding(
    FhirCodingMixin, TenantAuditMixin, Base
):
    """MeasureReport.group.stratifier.stratum.population.code.coding child table."""

    __tablename__ = "measure_report_group_stratifier_stratum_pop_code_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    stratum_population_id = Column(
        BigInteger,
        ForeignKey(
            "measure_report_group_stratifier_stratum_population.id", ondelete="CASCADE"
        ),
        nullable=False,
        index=True,
    )

    population = relationship(
        "MeasureReportGroupStratifierStratumPopulation", back_populates="code_coding"
    )
