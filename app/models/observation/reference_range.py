from sqlalchemy import BigInteger, Column, ForeignKey, Numeric, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin

# ---------------------------------------------------------------------------
# referenceRange (0..*) BackboneElement
# ---------------------------------------------------------------------------


class ObservationReferenceRange(TenantAuditMixin, Base):
    """Observation.referenceRange (0..*). `low`/`high` (each 0..1
    SimpleQuantity — no comparator column, SimpleQuantity forbids it) and
    `age` (0..1 Range of SimpleQuantity) are flattened; `type` (0..1
    CodeableConcept) is flattened with `_text` here, its own `coding[]`
    promoted to a direct-child table; `appliesTo` (0..* CodeableConcept)
    gets its own child table with a grandchild coding table."""

    __tablename__ = "observation_reference_range"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    observation_pk = Column(BigInteger, ForeignKey("observation.id"), nullable=False, index=True)

    low_value = Column(Numeric, nullable=True)
    low_unit = Column(String, nullable=True)
    low_system = Column(String, nullable=True)
    low_code = Column(String, nullable=True)

    high_value = Column(Numeric, nullable=True)
    high_unit = Column(String, nullable=True)
    high_system = Column(String, nullable=True)
    high_code = Column(String, nullable=True)

    type_text = Column(String, nullable=True)

    age_low_value = Column(Numeric, nullable=True)
    age_low_unit = Column(String, nullable=True)
    age_low_system = Column(String, nullable=True)
    age_low_code = Column(String, nullable=True)
    age_high_value = Column(Numeric, nullable=True)
    age_high_unit = Column(String, nullable=True)
    age_high_system = Column(String, nullable=True)
    age_high_code = Column(String, nullable=True)

    text = Column(String, nullable=True)

    observation = relationship("ObservationModel", back_populates="reference_ranges")
    type_codings = relationship(
        "ObservationReferenceRangeTypeCoding", back_populates="reference_range", cascade="all, delete-orphan"
    )
    applies_tos = relationship(
        "ObservationReferenceRangeAppliesTo", back_populates="reference_range", cascade="all, delete-orphan"
    )


class ObservationReferenceRangeTypeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Observation.referenceRange.type.coding (0..*)."""

    __tablename__ = "observation_reference_range_type_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    observation_reference_range_id = Column(
        BigInteger, ForeignKey("observation_reference_range.id"), nullable=False, index=True
    )

    reference_range = relationship("ObservationReferenceRange", back_populates="type_codings")


class ObservationReferenceRangeAppliesTo(TenantAuditMixin, Base):
    """One entry of Observation.referenceRange.appliesTo (0..* CodeableConcept)."""

    __tablename__ = "observation_reference_range_applies_to"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    observation_reference_range_id = Column(
        BigInteger, ForeignKey("observation_reference_range.id"), nullable=False, index=True
    )
    text = Column(String, nullable=True)

    reference_range = relationship("ObservationReferenceRange", back_populates="applies_tos")
    codings = relationship(
        "ObservationReferenceRangeAppliesToCoding", back_populates="applies_to", cascade="all, delete-orphan"
    )


class ObservationReferenceRangeAppliesToCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Observation.referenceRange.appliesTo.coding (0..*)."""

    __tablename__ = "observation_reference_range_applies_to_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    observation_reference_range_applies_to_id = Column(
        BigInteger, ForeignKey("observation_reference_range_applies_to.id"), nullable=False, index=True
    )

    applies_to = relationship("ObservationReferenceRangeAppliesTo", back_populates="codings")
