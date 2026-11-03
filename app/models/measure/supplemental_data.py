from sqlalchemy import BigInteger, Column, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class MeasureSupplementalData(TenantAuditMixin, Base):
    """Measure.supplementalData (0..* BackboneElement) child table."""

    __tablename__ = "measure_supplemental_data"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    measure_pk = Column(
        BigInteger, ForeignKey("measure.id", ondelete="CASCADE"), nullable=False, index=True
    )
    code_text = Column(String, nullable=True)
    description = Column(String, nullable=True)

    # criteria (1..1 Expression)
    criteria_description = Column(String, nullable=True)
    criteria_name = Column(String, nullable=True)
    criteria_language = Column(String, nullable=True)
    criteria_expression = Column(Text, nullable=True)
    criteria_reference = Column(String, nullable=True)

    measure = relationship("MeasureModel", back_populates="supplemental_data")
    code_codings = relationship(
        "MeasureSupplementalDataCodeCoding",
        back_populates="supplemental_data",
        cascade="all, delete-orphan",
    )
    usages = relationship(
        "MeasureSupplementalDataUsage",
        back_populates="supplemental_data",
        cascade="all, delete-orphan",
    )


class MeasureSupplementalDataCodeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """Coding within Measure.supplementalData.code."""

    __tablename__ = "measure_supplemental_data_code_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    measure_supplemental_data_id = Column(
        BigInteger,
        ForeignKey("measure_supplemental_data.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    supplemental_data = relationship("MeasureSupplementalData", back_populates="code_codings")


class MeasureSupplementalDataUsage(TenantAuditMixin, Base):
    """Measure.supplementalData.usage (0..* CodeableConcept) child table."""

    __tablename__ = "measure_supplemental_data_usage"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    measure_supplemental_data_id = Column(
        BigInteger,
        ForeignKey("measure_supplemental_data.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    text = Column(String, nullable=True)

    supplemental_data = relationship("MeasureSupplementalData", back_populates="usages")
    codings = relationship(
        "MeasureSupplementalDataUsageCoding",
        back_populates="usage",
        cascade="all, delete-orphan",
    )


class MeasureSupplementalDataUsageCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """Coding within Measure.supplementalData.usage."""

    __tablename__ = "measure_supplemental_data_usage_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    measure_supplemental_data_usage_id = Column(
        BigInteger,
        ForeignKey("measure_supplemental_data_usage.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    usage = relationship("MeasureSupplementalDataUsage", back_populates="codings")
