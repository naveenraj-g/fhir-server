from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    String,
)
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.enums import IdentifierUse
from app.models.shared import FhirCodingMixin, TenantAuditMixin
from app.models.specimen.enums import SpecimenAdditiveReferenceType


class SpecimenProcessing(TenantAuditMixin, Base):
    """One entry of Specimen.processing (0..* BackboneElement)."""

    __tablename__ = "specimen_processing"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    specimen_pk = Column(
        BigInteger, ForeignKey("specimen.id"), nullable=False, index=True
    )

    description = Column(String, nullable=True)
    procedure_text = Column(String, nullable=True)
    time_date_time = Column(DateTime(timezone=True), nullable=True)
    time_period_start = Column(DateTime(timezone=True), nullable=True)
    time_period_end = Column(DateTime(timezone=True), nullable=True)

    specimen = relationship("SpecimenModel", back_populates="processings")
    procedure_codings = relationship(
        "SpecimenProcessingProcedureCoding",
        back_populates="processing",
        cascade="all, delete-orphan",
    )
    additives = relationship(
        "SpecimenProcessingAdditive",
        back_populates="processing",
        cascade="all, delete-orphan",
    )


class SpecimenProcessingProcedureCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Specimen.processing.procedure.coding (0..*)."""

    __tablename__ = "specimen_processing_procedure_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    specimen_processing_id = Column(
        BigInteger,
        ForeignKey("specimen_processing.id"),
        nullable=False,
        index=True,
    )

    processing = relationship("SpecimenProcessing", back_populates="procedure_codings")


class SpecimenProcessingAdditive(TenantAuditMixin, Base):
    """One entry of Specimen.processing.additive (0..* Reference(Substance))."""

    __tablename__ = "specimen_processing_additive"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    specimen_processing_id = Column(
        BigInteger,
        ForeignKey("specimen_processing.id"),
        nullable=False,
        index=True,
    )

    reference_reference = Column(String, nullable=True)
    reference_type = Column(
        Enum(
            SpecimenAdditiveReferenceType,
            name="specimen_additive_reference_type",
        ),
        nullable=True,
    )
    reference_id = Column(BigInteger, nullable=True, index=True)
    reference_display = Column(String, nullable=True)

    # Reference identifier fallback
    reference_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    reference_identifier_system = Column(String, nullable=True)
    reference_identifier_value = Column(String, nullable=True)
    reference_identifier_type_text = Column(String, nullable=True)

    processing = relationship("SpecimenProcessing", back_populates="additives")
