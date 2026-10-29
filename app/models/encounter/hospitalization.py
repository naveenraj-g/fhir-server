from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.encounter.enums import EncounterHospitalizationReferenceType
from app.models.enums import IdentifierUse, OrganizationReferenceType
from app.models.shared import FhirCodingMixin, TenantAuditMixin

# ---------------------------------------------------------------------------
# hospitalization (0..1) BackboneElement child table
# ---------------------------------------------------------------------------


class EncounterHospitalization(TenantAuditMixin, Base):
    """hospitalization — details about the admission to a healthcare
    service. 0..1 on Encounter (`uselist=False` on the parent's own
    relationship) — the `UniqueConstraint` on `encounter_pk` below
    enforces "at most one" at the DB level, same as any ordinary 1:0..1
    relationship; this is an ordinary DB-design constraint, not a FHIR
    structural rule, so it's not in tension with this codebase's
    "no DB CheckConstraints for FHIR rules" policy (see OrganizationModel's
    docstring) — that policy is about R4 invariants like apr-1, not about
    plain relationship cardinality.

    `preAdmissionIdentifier` (0..1 Identifier) is flattened directly onto
    this row (`pre_admission_identifier_*`) since it's a single embed, not
    a list — its own `type.coding[]` is still promoted to a dedicated
    grandchild table (EncounterHospitalizationPreAdmissionIdentifierTypeCoding,
    below), and its own `assigner` (Reference(Organization)) gets the
    standard flattened-reference + identifier-fallback shape, same as
    every other Identifier.assigner in this codebase.

    `origin`/`destination` (each 0..1 Reference(Location|Organization))
    share `EncounterHospitalizationReferenceType` — both targets ARE
    modeled resources here, so both references are actually validated.

    `admitSource`/`reAdmission`/`dischargeDisposition` are each a 0..1
    CodeableConcept — text flattened, coding[] promoted to a dedicated
    child table each.

    `dietPreference`/`specialCourtesy`/`specialArrangement` are each 0..*
    CodeableConcept — 3-level-deep nesting (Encounter -> Hospitalization
    -> <field> -> Coding), same shape and same eager-load requirement as
    Appointment.participant.type (see CLAUDE.md's "nests 3 levels deep"
    invariant) — each gets its own child + grandchild table pair.
    """

    __tablename__ = "encounter_hospitalization"
    __table_args__ = (
        UniqueConstraint("encounter_pk", name="uq_encounter_hospitalization_encounter_pk"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    encounter_pk = Column(
        BigInteger, ForeignKey("encounter.id"), nullable=False, index=True
    )

    # ── preAdmissionIdentifier (0..1 Identifier) ──────────────────────────

    pre_admission_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use"), nullable=True
    )
    pre_admission_identifier_type_text = Column(String, nullable=True)
    pre_admission_identifier_system = Column(String, nullable=True)
    pre_admission_identifier_value = Column(String, nullable=True)
    pre_admission_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    pre_admission_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    pre_admission_identifier_assigner_reference = Column(String, nullable=True)
    pre_admission_identifier_assigner_type = Column(
        Enum(
            OrganizationReferenceType,
            name="organization_reference_type",
            create_type=False,
        ),
        nullable=True,
    )
    pre_admission_identifier_assigner_id = Column(BigInteger, nullable=True, index=True)
    pre_admission_identifier_assigner_display = Column(String, nullable=True)

    pre_admission_identifier_assigner_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use"), nullable=True
    )
    pre_admission_identifier_assigner_identifier_type_system = Column(String, nullable=True)
    pre_admission_identifier_assigner_identifier_type_version = Column(String, nullable=True)
    pre_admission_identifier_assigner_identifier_type_code = Column(String, nullable=True)
    pre_admission_identifier_assigner_identifier_type_display = Column(String, nullable=True)
    pre_admission_identifier_assigner_identifier_type_text = Column(String, nullable=True)
    pre_admission_identifier_assigner_identifier_type_user_selected = Column(Boolean, nullable=True)
    pre_admission_identifier_assigner_identifier_system = Column(String, nullable=True)
    pre_admission_identifier_assigner_identifier_value = Column(String, nullable=True)
    pre_admission_identifier_assigner_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    pre_admission_identifier_assigner_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    # ── origin (0..1 Reference(Location|Organization)) ───────────────────

    origin_reference = Column(String, nullable=True)
    origin_type = Column(
        Enum(EncounterHospitalizationReferenceType, name="encounter_hospitalization_reference_type"),
        nullable=True,
    )
    origin_id = Column(BigInteger, nullable=True, index=True)
    origin_display = Column(String, nullable=True)

    origin_identifier_use = Column(Enum(IdentifierUse, name="identifier_use"), nullable=True)
    origin_identifier_type_system = Column(String, nullable=True)
    origin_identifier_type_version = Column(String, nullable=True)
    origin_identifier_type_code = Column(String, nullable=True)
    origin_identifier_type_display = Column(String, nullable=True)
    origin_identifier_type_text = Column(String, nullable=True)
    origin_identifier_type_user_selected = Column(Boolean, nullable=True)
    origin_identifier_system = Column(String, nullable=True)
    origin_identifier_value = Column(String, nullable=True)
    origin_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    origin_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    # ── admitSource (0..1 CodeableConcept) ────────────────────────────────

    admit_source_text = Column(String, nullable=True)

    # ── reAdmission (0..1 CodeableConcept) ────────────────────────────────

    re_admission_text = Column(String, nullable=True)

    # ── destination (0..1 Reference(Location|Organization)) ──────────────

    destination_reference = Column(String, nullable=True)
    destination_type = Column(
        Enum(
            EncounterHospitalizationReferenceType,
            name="encounter_hospitalization_reference_type",
            create_type=False,
        ),
        nullable=True,
    )
    destination_id = Column(BigInteger, nullable=True, index=True)
    destination_display = Column(String, nullable=True)

    destination_identifier_use = Column(Enum(IdentifierUse, name="identifier_use"), nullable=True)
    destination_identifier_type_system = Column(String, nullable=True)
    destination_identifier_type_version = Column(String, nullable=True)
    destination_identifier_type_code = Column(String, nullable=True)
    destination_identifier_type_display = Column(String, nullable=True)
    destination_identifier_type_text = Column(String, nullable=True)
    destination_identifier_type_user_selected = Column(Boolean, nullable=True)
    destination_identifier_system = Column(String, nullable=True)
    destination_identifier_value = Column(String, nullable=True)
    destination_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    destination_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    # ── dischargeDisposition (0..1 CodeableConcept) ───────────────────────

    discharge_disposition_text = Column(String, nullable=True)

    encounter = relationship("EncounterModel", back_populates="hospitalization")

    pre_admission_identifier_type_codings = relationship(
        "EncounterHospitalizationPreAdmissionIdentifierTypeCoding",
        back_populates="hospitalization",
        cascade="all, delete-orphan",
    )
    admit_source_codings = relationship(
        "EncounterHospitalizationAdmitSourceCoding",
        back_populates="hospitalization",
        cascade="all, delete-orphan",
    )
    re_admission_codings = relationship(
        "EncounterHospitalizationReAdmissionCoding",
        back_populates="hospitalization",
        cascade="all, delete-orphan",
    )
    diet_preferences = relationship(
        "EncounterHospitalizationDietPreference",
        back_populates="hospitalization",
        cascade="all, delete-orphan",
    )
    special_courtesies = relationship(
        "EncounterHospitalizationSpecialCourtesy",
        back_populates="hospitalization",
        cascade="all, delete-orphan",
    )
    special_arrangements = relationship(
        "EncounterHospitalizationSpecialArrangement",
        back_populates="hospitalization",
        cascade="all, delete-orphan",
    )
    discharge_disposition_codings = relationship(
        "EncounterHospitalizationDischargeDispositionCoding",
        back_populates="hospitalization",
        cascade="all, delete-orphan",
    )


class EncounterHospitalizationPreAdmissionIdentifierTypeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Encounter.hospitalization.preAdmissionIdentifier.type.coding (0..*)."""

    __tablename__ = "encounter_hospitalization_pre_admission_identifier_type_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    encounter_hospitalization_id = Column(
        BigInteger, ForeignKey("encounter_hospitalization.id"), nullable=False, index=True
    )

    hospitalization = relationship(
        "EncounterHospitalization", back_populates="pre_admission_identifier_type_codings"
    )


class EncounterHospitalizationAdmitSourceCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Encounter.hospitalization.admitSource.coding (0..*)."""

    __tablename__ = "encounter_hospitalization_admit_source_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    encounter_hospitalization_id = Column(
        BigInteger, ForeignKey("encounter_hospitalization.id"), nullable=False, index=True
    )

    hospitalization = relationship(
        "EncounterHospitalization", back_populates="admit_source_codings"
    )


class EncounterHospitalizationReAdmissionCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Encounter.hospitalization.reAdmission.coding (0..*)."""

    __tablename__ = "encounter_hospitalization_re_admission_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    encounter_hospitalization_id = Column(
        BigInteger, ForeignKey("encounter_hospitalization.id"), nullable=False, index=True
    )

    hospitalization = relationship(
        "EncounterHospitalization", back_populates="re_admission_codings"
    )


class EncounterHospitalizationDischargeDispositionCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Encounter.hospitalization.dischargeDisposition.coding (0..*)."""

    __tablename__ = "encounter_hospitalization_discharge_disposition_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    encounter_hospitalization_id = Column(
        BigInteger, ForeignKey("encounter_hospitalization.id"), nullable=False, index=True
    )

    hospitalization = relationship(
        "EncounterHospitalization", back_populates="discharge_disposition_codings"
    )


# ---------------------------------------------------------------------------
# dietPreference (0..*) CodeableConcept child + grandchild
# ---------------------------------------------------------------------------


class EncounterHospitalizationDietPreference(TenantAuditMixin, Base):
    """One entry of Encounter.hospitalization.dietPreference (0..*)."""

    __tablename__ = "encounter_hospitalization_diet_preference"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    encounter_hospitalization_id = Column(
        BigInteger, ForeignKey("encounter_hospitalization.id"), nullable=False, index=True
    )
    text = Column(String, nullable=True)

    hospitalization = relationship("EncounterHospitalization", back_populates="diet_preferences")
    codings = relationship(
        "EncounterHospitalizationDietPreferenceCoding",
        back_populates="diet_preference",
        cascade="all, delete-orphan",
    )


class EncounterHospitalizationDietPreferenceCoding(FhirCodingMixin, TenantAuditMixin, Base):
    __tablename__ = "encounter_hospitalization_diet_preference_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    encounter_hospitalization_diet_preference_id = Column(
        BigInteger, ForeignKey("encounter_hospitalization_diet_preference.id"), nullable=False, index=True
    )

    diet_preference = relationship("EncounterHospitalizationDietPreference", back_populates="codings")


# ---------------------------------------------------------------------------
# specialCourtesy (0..*) CodeableConcept child + grandchild
# ---------------------------------------------------------------------------


class EncounterHospitalizationSpecialCourtesy(TenantAuditMixin, Base):
    """One entry of Encounter.hospitalization.specialCourtesy (0..*)."""

    __tablename__ = "encounter_hospitalization_special_courtesy"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    encounter_hospitalization_id = Column(
        BigInteger, ForeignKey("encounter_hospitalization.id"), nullable=False, index=True
    )
    text = Column(String, nullable=True)

    hospitalization = relationship("EncounterHospitalization", back_populates="special_courtesies")
    codings = relationship(
        "EncounterHospitalizationSpecialCourtesyCoding",
        back_populates="special_courtesy",
        cascade="all, delete-orphan",
    )


class EncounterHospitalizationSpecialCourtesyCoding(FhirCodingMixin, TenantAuditMixin, Base):
    __tablename__ = "encounter_hospitalization_special_courtesy_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    encounter_hospitalization_special_courtesy_id = Column(
        BigInteger, ForeignKey("encounter_hospitalization_special_courtesy.id"), nullable=False, index=True
    )

    special_courtesy = relationship("EncounterHospitalizationSpecialCourtesy", back_populates="codings")


# ---------------------------------------------------------------------------
# specialArrangement (0..*) CodeableConcept child + grandchild
# ---------------------------------------------------------------------------


class EncounterHospitalizationSpecialArrangement(TenantAuditMixin, Base):
    """One entry of Encounter.hospitalization.specialArrangement (0..*)."""

    __tablename__ = "encounter_hospitalization_special_arrangement"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    encounter_hospitalization_id = Column(
        BigInteger, ForeignKey("encounter_hospitalization.id"), nullable=False, index=True
    )
    text = Column(String, nullable=True)

    hospitalization = relationship("EncounterHospitalization", back_populates="special_arrangements")
    codings = relationship(
        "EncounterHospitalizationSpecialArrangementCoding",
        back_populates="special_arrangement",
        cascade="all, delete-orphan",
    )


class EncounterHospitalizationSpecialArrangementCoding(FhirCodingMixin, TenantAuditMixin, Base):
    __tablename__ = "encounter_hospitalization_special_arrangement_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    encounter_hospitalization_special_arrangement_id = Column(
        BigInteger, ForeignKey("encounter_hospitalization_special_arrangement.id"), nullable=False, index=True
    )

    special_arrangement = relationship("EncounterHospitalizationSpecialArrangement", back_populates="codings")
