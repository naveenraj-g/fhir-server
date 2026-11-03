from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class MeasureSubjectCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """Coding within Measure.subjectCodeableConcept."""

    __tablename__ = "measure_subject_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    measure_pk = Column(
        BigInteger, ForeignKey("measure.id", ondelete="CASCADE"), nullable=False, index=True
    )

    measure = relationship("MeasureModel", back_populates="subject_codings")


class MeasureScoringCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """Coding within Measure.scoring."""

    __tablename__ = "measure_scoring_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    measure_pk = Column(
        BigInteger, ForeignKey("measure.id", ondelete="CASCADE"), nullable=False, index=True
    )

    measure = relationship("MeasureModel", back_populates="scoring_codings")


class MeasureCompositeScoringCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """Coding within Measure.compositeScoring."""

    __tablename__ = "measure_composite_scoring_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    measure_pk = Column(
        BigInteger, ForeignKey("measure.id", ondelete="CASCADE"), nullable=False, index=True
    )

    measure = relationship("MeasureModel", back_populates="composite_scoring_codings")


class MeasureImprovementNotationCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """Coding within Measure.improvementNotation."""

    __tablename__ = "measure_improvement_notation_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    measure_pk = Column(
        BigInteger, ForeignKey("measure.id", ondelete="CASCADE"), nullable=False, index=True
    )

    measure = relationship("MeasureModel", back_populates="improvement_notation_codings")


class MeasureType(TenantAuditMixin, Base):
    """Measure.type (0..* CodeableConcept) child table."""

    __tablename__ = "measure_type"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    measure_pk = Column(
        BigInteger, ForeignKey("measure.id", ondelete="CASCADE"), nullable=False, index=True
    )
    text = Column(String, nullable=True)

    measure = relationship("MeasureModel", back_populates="types")
    codings = relationship(
        "MeasureTypeCoding",
        back_populates="measure_type",
        cascade="all, delete-orphan",
    )


class MeasureTypeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """Coding within Measure.type."""

    __tablename__ = "measure_type_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    measure_type_id = Column(
        BigInteger,
        ForeignKey("measure_type.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    measure_type = relationship("MeasureType", back_populates="codings")


class MeasureTopic(TenantAuditMixin, Base):
    """Measure.topic (0..* CodeableConcept) child table."""

    __tablename__ = "measure_topic"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    measure_pk = Column(
        BigInteger, ForeignKey("measure.id", ondelete="CASCADE"), nullable=False, index=True
    )
    text = Column(String, nullable=True)

    measure = relationship("MeasureModel", back_populates="topics")
    codings = relationship(
        "MeasureTopicCoding",
        back_populates="measure_topic",
        cascade="all, delete-orphan",
    )


class MeasureTopicCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """Coding within Measure.topic."""

    __tablename__ = "measure_topic_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    measure_topic_id = Column(
        BigInteger,
        ForeignKey("measure_topic.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    measure_topic = relationship("MeasureTopic", back_populates="codings")


class MeasureJurisdiction(TenantAuditMixin, Base):
    """Measure.jurisdiction (0..* CodeableConcept) child table."""

    __tablename__ = "measure_jurisdiction"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    measure_pk = Column(
        BigInteger, ForeignKey("measure.id", ondelete="CASCADE"), nullable=False, index=True
    )
    text = Column(String, nullable=True)

    measure = relationship("MeasureModel", back_populates="jurisdictions")
    codings = relationship(
        "MeasureJurisdictionCoding",
        back_populates="measure_jurisdiction",
        cascade="all, delete-orphan",
    )


class MeasureJurisdictionCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """Coding within Measure.jurisdiction."""

    __tablename__ = "measure_jurisdiction_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    measure_jurisdiction_id = Column(
        BigInteger,
        ForeignKey("measure_jurisdiction.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    measure_jurisdiction = relationship("MeasureJurisdiction", back_populates="codings")
