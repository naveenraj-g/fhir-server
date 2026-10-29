from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.encounter.enums import EncounterConditionOrProcedureReferenceType
from app.models.enums import IdentifierUse
from app.models.shared import FhirCodingMixin, TenantAuditMixin

# ---------------------------------------------------------------------------
# diagnosis (0..*) BackboneElement child table
# ---------------------------------------------------------------------------


class EncounterDiagnosis(TenantAuditMixin, Base):
    """diagnosis[] — the list of diagnosis relevant to this encounter.

    `condition` (1..1 Reference(Condition|Procedure)) is required per
    spec but modeled as nullable here, same as every other flattened
    Reference field (the "required" structural rule is enforced by the
    FHIR validator, not a DB NOT NULL — see OrganizationModel's
    docstring) — neither Condition nor Procedure is a modeled resource
    in this system, so this reference's existence check is never
    attempted.

    `use` (0..1 CodeableConcept) — text flattened here, coding[]
    promoted to a dedicated child table (EncounterDiagnosisUseCoding,
    below). `rank` (0..1 positiveInt)."""

    __tablename__ = "encounter_diagnosis"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    encounter_pk = Column(
        BigInteger, ForeignKey("encounter.id"), nullable=False, index=True
    )

    # ── condition (1..1 Reference, polymorphic) ───────────────────────────

    condition_reference = Column(String, nullable=True)
    condition_type = Column(
        Enum(
            EncounterConditionOrProcedureReferenceType,
            name="encounter_condition_or_procedure_reference_type",
        ),
        nullable=True,
    )
    condition_id = Column(BigInteger, nullable=True, index=True)
    condition_display = Column(String, nullable=True)

    condition_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use"), nullable=True
    )
    condition_identifier_type_system = Column(String, nullable=True)
    condition_identifier_type_version = Column(String, nullable=True)
    condition_identifier_type_code = Column(String, nullable=True)
    condition_identifier_type_display = Column(String, nullable=True)
    condition_identifier_type_text = Column(String, nullable=True)
    condition_identifier_type_user_selected = Column(Boolean, nullable=True)
    condition_identifier_system = Column(String, nullable=True)
    condition_identifier_value = Column(String, nullable=True)
    condition_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    condition_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    # ── use (0..1 CodeableConcept) ─────────────────────────────────────────

    use_text = Column(String, nullable=True)

    # ── rank (0..1 positiveInt) ────────────────────────────────────────────

    rank = Column(Integer, nullable=True)

    encounter = relationship("EncounterModel", back_populates="diagnoses")
    use_codings = relationship(
        "EncounterDiagnosisUseCoding", back_populates="diagnosis", cascade="all, delete-orphan"
    )


class EncounterDiagnosisUseCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Encounter.diagnosis.use.coding (0..*)."""

    __tablename__ = "encounter_diagnosis_use_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    encounter_diagnosis_id = Column(
        BigInteger, ForeignKey("encounter_diagnosis.id"), nullable=False, index=True
    )

    diagnosis = relationship("EncounterDiagnosis", back_populates="use_codings")
