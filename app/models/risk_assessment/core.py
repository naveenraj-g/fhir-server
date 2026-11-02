from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    Sequence,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.enums import (
    EncounterReferenceType,
    IdentifierUse,
    SubjectReferenceType,
)
from app.models.risk_assessment.enums import (
    RiskAssessmentConditionReferenceType,
    RiskAssessmentPerformerReferenceType,
    RiskAssessmentStatus,
)
from app.models.shared import TenantAuditMixin

risk_assessment_id_seq = Sequence(
    "risk_assessment_pub_seq", start=520000, increment=1, metadata=Base.metadata
)


class RiskAssessmentModel(TenantAuditMixin, Base):
    """FHIR R4 RiskAssessment — https://www.hl7.org/fhir/R4/riskassessment.html

    An assessment of the likely outcome(s) for a patient or other subject as well
    as the likelihood of each outcome.

    JWT / RBAC pattern — org-scoped via `tenant_id`, strictly NO `user_id`.
    """

    __tablename__ = "risk_assessment"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    risk_assessment_id = Column(
        BigInteger,
        risk_assessment_id_seq,
        nullable=False,
        unique=True,
        index=True,
    )

    # Resource-level extension support (0..* Extension)
    extension = Column(JSONB, nullable=False, server_default=text("'[]'"))

    # status (1..1 code, required)
    status = Column(
        Enum(
            RiskAssessmentStatus,
            name="risk_assessment_status",
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=False,
    )

    # method (0..1 CodeableConcept) — text flat on main table
    method_text = Column(String, nullable=True)

    # code (0..1 CodeableConcept) — text flat on main table
    code_text = Column(String, nullable=True)

    # subject (1..1 Reference(Patient | Group))
    subject_reference = Column(String, nullable=True)
    subject_type = Column(
        Enum(SubjectReferenceType, name="subject_reference_type", create_type=False),
        nullable=True,
    )
    subject_id = Column(BigInteger, nullable=True, index=True)
    subject_display = Column(String, nullable=True)

    subject_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    subject_identifier_type_system = Column(String, nullable=True)
    subject_identifier_type_version = Column(String, nullable=True)
    subject_identifier_type_code = Column(String, nullable=True)
    subject_identifier_type_display = Column(String, nullable=True)
    subject_identifier_type_user_selected = Column(Boolean, nullable=True)
    subject_identifier_type_text = Column(String, nullable=True)
    subject_identifier_system = Column(String, nullable=True)
    subject_identifier_value = Column(String, nullable=True)
    subject_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    subject_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    # basedOn (0..1 Reference(Any)) — open reference
    based_on_reference = Column(String, nullable=True)
    based_on_type = Column(String, nullable=True)
    based_on_id = Column(BigInteger, nullable=True, index=True)
    based_on_display = Column(String, nullable=True)

    based_on_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    based_on_identifier_type_system = Column(String, nullable=True)
    based_on_identifier_type_version = Column(String, nullable=True)
    based_on_identifier_type_code = Column(String, nullable=True)
    based_on_identifier_type_display = Column(String, nullable=True)
    based_on_identifier_type_user_selected = Column(Boolean, nullable=True)
    based_on_identifier_type_text = Column(String, nullable=True)
    based_on_identifier_system = Column(String, nullable=True)
    based_on_identifier_value = Column(String, nullable=True)
    based_on_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    based_on_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    # parent (0..1 Reference(Any)) — open reference
    parent_reference = Column(String, nullable=True)
    parent_type = Column(String, nullable=True)
    parent_id = Column(BigInteger, nullable=True, index=True)
    parent_display = Column(String, nullable=True)

    parent_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    parent_identifier_type_system = Column(String, nullable=True)
    parent_identifier_type_version = Column(String, nullable=True)
    parent_identifier_type_code = Column(String, nullable=True)
    parent_identifier_type_display = Column(String, nullable=True)
    parent_identifier_type_user_selected = Column(Boolean, nullable=True)
    parent_identifier_type_text = Column(String, nullable=True)
    parent_identifier_system = Column(String, nullable=True)
    parent_identifier_value = Column(String, nullable=True)
    parent_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    parent_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    # encounter (0..1 Reference(Encounter))
    encounter_reference = Column(String, nullable=True)
    encounter_type = Column(
        Enum(EncounterReferenceType, name="encounter_reference_type", create_type=False),
        nullable=True,
    )
    encounter_id = Column(BigInteger, nullable=True, index=True)
    encounter_display = Column(String, nullable=True)

    encounter_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    encounter_identifier_type_system = Column(String, nullable=True)
    encounter_identifier_type_version = Column(String, nullable=True)
    encounter_identifier_type_code = Column(String, nullable=True)
    encounter_identifier_type_display = Column(String, nullable=True)
    encounter_identifier_type_user_selected = Column(Boolean, nullable=True)
    encounter_identifier_type_text = Column(String, nullable=True)
    encounter_identifier_system = Column(String, nullable=True)
    encounter_identifier_value = Column(String, nullable=True)
    encounter_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    encounter_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    # occurrence[x] (0..1 dateTime | Period)
    occurrence_date_time = Column(DateTime(timezone=True), nullable=True)
    occurrence_period_start = Column(DateTime(timezone=True), nullable=True)
    occurrence_period_end = Column(DateTime(timezone=True), nullable=True)

    # condition (0..1 Reference(Condition))
    condition_reference = Column(String, nullable=True)
    condition_type = Column(
        Enum(
            RiskAssessmentConditionReferenceType,
            name="risk_assessment_condition_reference_type",
        ),
        nullable=True,
    )
    condition_id = Column(BigInteger, nullable=True, index=True)
    condition_display = Column(String, nullable=True)

    condition_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    condition_identifier_type_system = Column(String, nullable=True)
    condition_identifier_type_version = Column(String, nullable=True)
    condition_identifier_type_code = Column(String, nullable=True)
    condition_identifier_type_display = Column(String, nullable=True)
    condition_identifier_type_user_selected = Column(Boolean, nullable=True)
    condition_identifier_type_text = Column(String, nullable=True)
    condition_identifier_system = Column(String, nullable=True)
    condition_identifier_value = Column(String, nullable=True)
    condition_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    condition_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    # performer (0..1 Reference(Practitioner | PractitionerRole | Device))
    performer_reference = Column(String, nullable=True)
    performer_type = Column(
        Enum(
            RiskAssessmentPerformerReferenceType,
            name="risk_assessment_performer_reference_type",
        ),
        nullable=True,
    )
    performer_id = Column(BigInteger, nullable=True, index=True)
    performer_display = Column(String, nullable=True)

    performer_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    performer_identifier_type_system = Column(String, nullable=True)
    performer_identifier_type_version = Column(String, nullable=True)
    performer_identifier_type_code = Column(String, nullable=True)
    performer_identifier_type_display = Column(String, nullable=True)
    performer_identifier_type_user_selected = Column(Boolean, nullable=True)
    performer_identifier_type_text = Column(String, nullable=True)
    performer_identifier_system = Column(String, nullable=True)
    performer_identifier_value = Column(String, nullable=True)
    performer_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    performer_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    # mitigation (0..1 string)
    mitigation = Column(Text, nullable=True)

    # ── Relationships ──────────────────────────────────────────────────────────
    identifiers = relationship(
        "RiskAssessmentIdentifierModel",
        back_populates="risk_assessment",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    method_codings = relationship(
        "RiskAssessmentMethodCodingModel",
        back_populates="risk_assessment",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    code_codings = relationship(
        "RiskAssessmentCodeCodingModel",
        back_populates="risk_assessment",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    reason_codes = relationship(
        "RiskAssessmentReasonCodeModel",
        back_populates="risk_assessment",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    reason_references = relationship(
        "RiskAssessmentReasonReferenceModel",
        back_populates="risk_assessment",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    basis = relationship(
        "RiskAssessmentBasisModel",
        back_populates="risk_assessment",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    predictions = relationship(
        "RiskAssessmentPredictionModel",
        back_populates="risk_assessment",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    notes = relationship(
        "RiskAssessmentNoteModel",
        back_populates="risk_assessment",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
