from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Enum,
    Sequence,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.allergy_intolerance.enums import (
    AllergyIntoleranceAsserterReferenceType,
    AllergyIntoleranceCategory,
    AllergyIntoleranceCriticality,
    AllergyIntoleranceEncounterReferenceType,
    AllergyIntolerancePatientReferenceType,
    AllergyIntoleranceRecorderReferenceType,
    AllergyIntoleranceType,
)
from app.models.shared import TenantAuditMixin


class AllergyIntoleranceModel(TenantAuditMixin, Base):
    """SQLAlchemy ORM model for FHIR R4 AllergyIntolerance resource."""

    __tablename__ = "allergy_intolerance"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    allergy_intolerance_id = Column(
        BigInteger,
        Sequence(
            "allergy_intolerance_pub_seq",
            start=260000,
            increment=1,
            metadata=Base.metadata,
        ),
        unique=True,
        index=True,
        nullable=False,
    )

    clinical_status_text = Column(String, nullable=True)
    verification_status_text = Column(String, nullable=True)

    type = Column(
        Enum(
            AllergyIntoleranceType,
            name="allergy_intolerance_type",
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=True,
    )
    category = Column(
        ARRAY(
            Enum(
                AllergyIntoleranceCategory,
                name="allergy_intolerance_category",
                values_callable=lambda enum_cls: [m.value for m in enum_cls],
            )
        ),
        nullable=True,
    )
    criticality = Column(
        Enum(
            AllergyIntoleranceCriticality,
            name="allergy_intolerance_criticality",
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=True,
    )

    code_text = Column(String, nullable=True)

    # Reference(Patient) - 1..1
    patient_reference = Column(String, nullable=False)
    patient_type = Column(
        Enum(
            AllergyIntolerancePatientReferenceType,
            name="allergy_intolerance_patient_reference_type",
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=False,
    )
    patient_id = Column(BigInteger, nullable=True)
    patient_display = Column(String, nullable=True)

    # Reference(Encounter) - 0..1
    encounter_reference = Column(String, nullable=True)
    encounter_type = Column(
        Enum(
            AllergyIntoleranceEncounterReferenceType,
            name="allergy_intolerance_encounter_reference_type",
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=True,
    )
    encounter_id = Column(BigInteger, nullable=True)
    encounter_display = Column(String, nullable=True)

    # Choice onset[x]: onsetDateTime, onsetAge, onsetPeriod, onsetRange, onsetString
    onset_date_time = Column(DateTime(timezone=True), nullable=True)
    onset_age = Column(JSONB, nullable=True)
    onset_period_start = Column(DateTime(timezone=True), nullable=True)
    onset_period_end = Column(DateTime(timezone=True), nullable=True)
    onset_range = Column(JSONB, nullable=True)
    onset_string = Column(String, nullable=True)

    recorded_date = Column(DateTime(timezone=True), nullable=True)

    # Reference(recorder) - 0..1
    recorder_reference = Column(String, nullable=True)
    recorder_type = Column(
        Enum(
            AllergyIntoleranceRecorderReferenceType,
            name="allergy_intolerance_recorder_reference_type",
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=True,
    )
    recorder_id = Column(BigInteger, nullable=True)
    recorder_display = Column(String, nullable=True)

    # Reference(asserter) - 0..1
    asserter_reference = Column(String, nullable=True)
    asserter_type = Column(
        Enum(
            AllergyIntoleranceAsserterReferenceType,
            name="allergy_intolerance_asserter_reference_type",
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=True,
    )
    asserter_id = Column(BigInteger, nullable=True)
    asserter_display = Column(String, nullable=True)

    last_occurrence = Column(DateTime(timezone=True), nullable=True)

    extension = Column(JSONB, nullable=False, server_default=text("'[]'"))

    # Relationships
    identifiers = relationship(
        "AllergyIntoleranceIdentifier",
        back_populates="allergy_intolerance",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    clinical_status_codings = relationship(
        "AllergyIntoleranceClinicalStatusCoding",
        back_populates="allergy_intolerance",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    verification_status_codings = relationship(
        "AllergyIntoleranceVerificationStatusCoding",
        back_populates="allergy_intolerance",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    code_codings = relationship(
        "AllergyIntoleranceCodeCoding",
        back_populates="allergy_intolerance",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    notes = relationship(
        "AllergyIntoleranceNote",
        back_populates="allergy_intolerance",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    reactions = relationship(
        "AllergyIntoleranceReaction",
        back_populates="allergy_intolerance",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
