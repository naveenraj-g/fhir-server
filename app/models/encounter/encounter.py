from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    Sequence,
    String,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import FHIRBase as Base
from app.models.encounter.enums import (
    EncounterAccountReferenceType,
    EncounterAppointmentReferenceType,
    EncounterBasedOnReferenceType,
    EncounterDiagnosisConditionType,
    EncounterEpisodeOfCareReferenceType,
    EncounterLocationReferenceType,
    EncounterLocationStatus,
    EncounterParticipantReferenceType,
    EncounterReasonReferenceType,
    EncounterStatus,
)
from app.models.enums import OrganizationReferenceType, SubjectReferenceType

encounter_id_seq = Sequence(
    "encounter_pub_seq", start=20000, increment=1, metadata=Base.metadata
)


class EncounterModel(Base):
    __tablename__ = "encounter"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    encounter_id = Column(
        Integer,
        encounter_id_seq,
        server_default=encounter_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    user_id = Column(String, nullable=True, index=True)
    org_id = Column(String, nullable=True, index=True)

    # status (1..1 code)
    status = Column(Enum(EncounterStatus, name="encounter_status"), nullable=True)

    # class (1..1 Coding) — flattened
    class_system = Column(String, nullable=True)
    class_code = Column(String, nullable=True)
    class_display = Column(String, nullable=True)

    # serviceType (0..1 CodeableConcept) — flattened
    service_type_system = Column(String, nullable=True)
    service_type_code = Column(String, nullable=True)
    service_type_display = Column(String, nullable=True)
    service_type_text = Column(String, nullable=True)

    # priority (0..1 CodeableConcept) — flattened
    priority_system = Column(String, nullable=True)
    priority_code = Column(String, nullable=True)
    priority_display = Column(String, nullable=True)
    priority_text = Column(String, nullable=True)

    # subject (0..1 Reference(Patient|Group))
    subject_type = Column(
        Enum(SubjectReferenceType, name="subject_reference_type"),
        nullable=True,
    )
    subject_id = Column(Integer, nullable=True)
    subject_display = Column(String, nullable=True)

    # period (0..1 Period)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    # length (0..1 Duration) — flattened
    length_value = Column(Float, nullable=True)
    length_comparator = Column(String, nullable=True)
    length_unit = Column(String, nullable=True)
    length_system = Column(String, nullable=True)
    length_code = Column(String, nullable=True)

    # serviceProvider (0..1 Reference(Organization)) — shared enum + FK
    service_provider_type = Column(
        Enum(
            OrganizationReferenceType,
            name="organization_reference_type",
            create_type=False,
        ),
        nullable=True,
    )
    service_provider_id = Column(Integer, ForeignKey("organization.id"), nullable=True, index=True)
    service_provider_display = Column(String, nullable=True)
    service_provider = relationship(
        "OrganizationModel", foreign_keys=[service_provider_id], lazy="selectin"
    )

    # partOf (0..1 Reference(Encounter)) — self-referential FK to internal PK
    part_of_id = Column(Integer, ForeignKey("encounter.id"), nullable=True, index=True)
    part_of = relationship(
        "EncounterModel", remote_side=[id], foreign_keys=[part_of_id], lazy="selectin"
    )

    # hospitalization (0..1 BackboneElement) — flattened
    # preAdmissionIdentifier (0..1 Identifier)
    hospitalization_pre_admission_identifier_system = Column(String, nullable=True)
    hospitalization_pre_admission_identifier_value = Column(String, nullable=True)
    # origin (0..1 Reference(Location|Organization))
    hospitalization_origin_type = Column(String, nullable=True)
    hospitalization_origin_id = Column(Integer, nullable=True)
    hospitalization_origin_display = Column(String, nullable=True)
    # admitSource (0..1 CodeableConcept)
    hospitalization_admit_source_system = Column(String, nullable=True)
    hospitalization_admit_source_code = Column(String, nullable=True)
    hospitalization_admit_source_display = Column(String, nullable=True)
    hospitalization_admit_source_text = Column(String, nullable=True)
    # reAdmission (0..1 CodeableConcept)
    hospitalization_re_admission_system = Column(String, nullable=True)
    hospitalization_re_admission_code = Column(String, nullable=True)
    hospitalization_re_admission_display = Column(String, nullable=True)
    hospitalization_re_admission_text = Column(String, nullable=True)
    # destination (0..1 Reference(Location|Organization))
    hospitalization_destination_type = Column(String, nullable=True)
    hospitalization_destination_id = Column(Integer, nullable=True)
    hospitalization_destination_display = Column(String, nullable=True)
    # dischargeDisposition (0..1 CodeableConcept)
    hospitalization_discharge_disposition_system = Column(String, nullable=True)
    hospitalization_discharge_disposition_code = Column(String, nullable=True)
    hospitalization_discharge_disposition_display = Column(String, nullable=True)
    hospitalization_discharge_disposition_text = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, nullable=True)
    updated_by = Column(String, nullable=True)

    # Relationships
    identifiers = relationship(
        "EncounterIdentifier", back_populates="encounter", cascade="all, delete-orphan"
    )
    status_history = relationship(
        "EncounterStatusHistory",
        back_populates="encounter",
        cascade="all, delete-orphan",
    )
    class_history = relationship(
        "EncounterClassHistory",
        back_populates="encounter",
        cascade="all, delete-orphan",
    )
    types = relationship(
        "EncounterType", back_populates="encounter", cascade="all, delete-orphan"
    )
    episode_of_cares = relationship(
        "EncounterEpisodeOfCare",
        back_populates="encounter",
        cascade="all, delete-orphan",
    )
    based_ons = relationship(
        "EncounterBasedOn", back_populates="encounter", cascade="all, delete-orphan"
    )
    participants = relationship(
        "EncounterParticipant", back_populates="encounter", cascade="all, delete-orphan"
    )
    appointment_refs = relationship(
        "EncounterAppointmentRef",
        back_populates="encounter",
        cascade="all, delete-orphan",
    )
    reason_codes = relationship(
        "EncounterReasonCode", back_populates="encounter", cascade="all, delete-orphan"
    )
    reason_references = relationship(
        "EncounterReasonReference", back_populates="encounter", cascade="all, delete-orphan"
    )
    diagnoses = relationship(
        "EncounterDiagnosis", back_populates="encounter", cascade="all, delete-orphan"
    )
    accounts = relationship(
        "EncounterAccount", back_populates="encounter", cascade="all, delete-orphan"
    )
    diet_preferences = relationship(
        "EncounterDietPreference",
        back_populates="encounter",
        cascade="all, delete-orphan",
    )
    special_arrangements = relationship(
        "EncounterSpecialArrangement",
        back_populates="encounter",
        cascade="all, delete-orphan",
    )
    special_courtesies = relationship(
        "EncounterSpecialCourtesy",
        back_populates="encounter",
        cascade="all, delete-orphan",
    )
    locations = relationship(
        "EncounterLocation", back_populates="encounter", cascade="all, delete-orphan"
    )


# ── Sub-resource tables ────────────────────────────────────────────────────────


class EncounterIdentifier(Base):
    __tablename__ = "encounter_identifier"

    id = Column(Integer, primary_key=True, autoincrement=True)
    encounter_id = Column(
        Integer, ForeignKey("encounter.id"), nullable=False, index=True
    )
    org_id = Column(String, nullable=True)

    use = Column(String, nullable=True)
    type_system = Column(String, nullable=True)
    type_code = Column(String, nullable=True)
    type_display = Column(String, nullable=True)
    type_text = Column(String, nullable=True)
    system = Column(String, nullable=True)
    value = Column(String, nullable=True)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)
    assigner = Column(String, nullable=True)

    encounter = relationship("EncounterModel", back_populates="identifiers")


class EncounterStatusHistory(Base):
    """statusHistory[] (0..* BackboneElement)."""

    __tablename__ = "encounter_status_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    encounter_id = Column(
        Integer, ForeignKey("encounter.id"), nullable=False, index=True
    )
    org_id = Column(String, nullable=True)

    status = Column(Enum(EncounterStatus, name="encounter_status", create_type=False), nullable=False)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    encounter = relationship("EncounterModel", back_populates="status_history")


class EncounterClassHistory(Base):
    """classHistory[] (0..* BackboneElement)."""

    __tablename__ = "encounter_class_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    encounter_id = Column(
        Integer, ForeignKey("encounter.id"), nullable=False, index=True
    )
    org_id = Column(String, nullable=True)

    class_system = Column(String, nullable=True)
    class_version = Column(String, nullable=True)
    class_code = Column(String, nullable=True)
    class_display = Column(String, nullable=True)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    encounter = relationship("EncounterModel", back_populates="class_history")


class EncounterType(Base):
    """type[] (0..*) CodeableConcept."""

    __tablename__ = "encounter_type"

    id = Column(Integer, primary_key=True, autoincrement=True)
    encounter_id = Column(
        Integer, ForeignKey("encounter.id"), nullable=False, index=True
    )
    org_id = Column(String, nullable=True)

    coding_system = Column(String, nullable=True)
    coding_code = Column(String, nullable=True)
    coding_display = Column(String, nullable=True)
    text = Column(String, nullable=True)

    encounter = relationship("EncounterModel", back_populates="types")


class EncounterEpisodeOfCare(Base):
    """episodeOfCare[] (0..*) Reference(EpisodeOfCare)."""

    __tablename__ = "encounter_episode_of_care"

    id = Column(Integer, primary_key=True, autoincrement=True)
    encounter_id = Column(
        Integer, ForeignKey("encounter.id"), nullable=False, index=True
    )
    org_id = Column(String, nullable=True)

    reference_type = Column(
        Enum(
            EncounterEpisodeOfCareReferenceType,
            name="encounter_episode_of_care_reference_type",
        ),
        nullable=True,
    )
    reference_id = Column(Integer, nullable=True)
    reference_display = Column(String, nullable=True)

    encounter = relationship("EncounterModel", back_populates="episode_of_cares")


class EncounterBasedOn(Base):
    """basedOn[] (0..*) Reference(ServiceRequest)."""

    __tablename__ = "encounter_based_on"

    id = Column(Integer, primary_key=True, autoincrement=True)
    encounter_id = Column(
        Integer, ForeignKey("encounter.id"), nullable=False, index=True
    )
    org_id = Column(String, nullable=True)

    reference_type = Column(
        Enum(EncounterBasedOnReferenceType, name="encounter_based_on_reference_type"),
        nullable=True,
    )
    reference_id = Column(Integer, nullable=True)
    reference_display = Column(String, nullable=True)

    encounter = relationship("EncounterModel", back_populates="based_ons")


class EncounterParticipant(Base):
    """participant[] (0..*) BackboneElement — individual (0..1 Reference(Practitioner|PractitionerRole|RelatedPerson))."""

    __tablename__ = "encounter_participant"

    id = Column(Integer, primary_key=True, autoincrement=True)
    encounter_id = Column(
        Integer, ForeignKey("encounter.id"), nullable=False, index=True
    )
    org_id = Column(String, nullable=True)

    # individual (0..1 Reference)
    reference_type = Column(
        Enum(
            EncounterParticipantReferenceType,
            name="encounter_participant_reference_type",
        ),
        nullable=True,
    )
    reference_id = Column(Integer, nullable=True)
    reference_display = Column(String, nullable=True)

    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    encounter = relationship("EncounterModel", back_populates="participants")
    types = relationship(
        "EncounterParticipantType",
        back_populates="participant",
        cascade="all, delete-orphan",
    )


class EncounterParticipantType(Base):
    """participant.type[] (0..*) CodeableConcept."""

    __tablename__ = "encounter_participant_type"

    id = Column(Integer, primary_key=True, autoincrement=True)
    participant_id = Column(
        Integer, ForeignKey("encounter_participant.id"), nullable=False, index=True
    )
    org_id = Column(String, nullable=True)

    coding_system = Column(String, nullable=True)
    coding_code = Column(String, nullable=True)
    coding_display = Column(String, nullable=True)
    text = Column(String, nullable=True)

    participant = relationship("EncounterParticipant", back_populates="types")


class EncounterAppointmentRef(Base):
    """appointment[] (0..*) Reference(Appointment)."""

    __tablename__ = "encounter_appointment_ref"

    id = Column(Integer, primary_key=True, autoincrement=True)
    encounter_id = Column(
        Integer, ForeignKey("encounter.id"), nullable=False, index=True
    )
    org_id = Column(String, nullable=True)

    reference_type = Column(
        Enum(
            EncounterAppointmentReferenceType,
            name="encounter_appointment_ref_reference_type",
        ),
        nullable=True,
    )
    reference_id = Column(Integer, nullable=True)
    reference_display = Column(String, nullable=True)

    encounter = relationship("EncounterModel", back_populates="appointment_refs")


class EncounterReasonCode(Base):
    """reasonCode[] (0..*) CodeableConcept."""

    __tablename__ = "encounter_reason_code"

    id = Column(Integer, primary_key=True, autoincrement=True)
    encounter_id = Column(
        Integer, ForeignKey("encounter.id"), nullable=False, index=True
    )
    org_id = Column(String, nullable=True)

    coding_system = Column(String, nullable=True)
    coding_code = Column(String, nullable=True)
    coding_display = Column(String, nullable=True)
    text = Column(String, nullable=True)

    encounter = relationship("EncounterModel", back_populates="reason_codes")


class EncounterReasonReference(Base):
    """reasonReference[] (0..*) Reference(Condition|Procedure|Observation|ImmunizationRecommendation)."""

    __tablename__ = "encounter_reason_reference"

    id = Column(Integer, primary_key=True, autoincrement=True)
    encounter_id = Column(
        Integer, ForeignKey("encounter.id"), nullable=False, index=True
    )
    org_id = Column(String, nullable=True)

    reference_type = Column(
        Enum(EncounterReasonReferenceType, name="encounter_reason_reference_type"),
        nullable=True,
    )
    reference_id = Column(Integer, nullable=True)
    reference_display = Column(String, nullable=True)

    encounter = relationship("EncounterModel", back_populates="reason_references")


class EncounterDiagnosis(Base):
    """diagnosis[] (0..*) BackboneElement — condition (1..1 Reference(Condition|Procedure)), use (0..1 CodeableConcept), rank (0..1 positiveInt)."""

    __tablename__ = "encounter_diagnosis"

    id = Column(Integer, primary_key=True, autoincrement=True)
    encounter_id = Column(
        Integer, ForeignKey("encounter.id"), nullable=False, index=True
    )
    org_id = Column(String, nullable=True)

    # condition (1..1 Reference(Condition|Procedure))
    condition_type = Column(
        Enum(EncounterDiagnosisConditionType, name="encounter_diagnosis_condition_type"),
        nullable=True,
    )
    condition_id = Column(Integer, nullable=True)
    condition_display = Column(String, nullable=True)

    # use (0..1 CodeableConcept)
    use_system = Column(String, nullable=True)
    use_code = Column(String, nullable=True)
    use_display = Column(String, nullable=True)
    use_text = Column(String, nullable=True)

    # rank (0..1 positiveInt)
    rank = Column(Integer, nullable=True)

    encounter = relationship("EncounterModel", back_populates="diagnoses")


class EncounterAccount(Base):
    """account[] (0..*) Reference(Account)."""

    __tablename__ = "encounter_account"

    id = Column(Integer, primary_key=True, autoincrement=True)
    encounter_id = Column(
        Integer, ForeignKey("encounter.id"), nullable=False, index=True
    )
    org_id = Column(String, nullable=True)

    reference_type = Column(
        Enum(EncounterAccountReferenceType, name="encounter_account_reference_type"),
        nullable=True,
    )
    reference_id = Column(Integer, nullable=True)
    reference_display = Column(String, nullable=True)

    encounter = relationship("EncounterModel", back_populates="accounts")


class EncounterDietPreference(Base):
    """hospitalization.dietPreference[] (0..*) CodeableConcept."""

    __tablename__ = "encounter_diet_preference"

    id = Column(Integer, primary_key=True, autoincrement=True)
    encounter_id = Column(
        Integer, ForeignKey("encounter.id"), nullable=False, index=True
    )
    org_id = Column(String, nullable=True)

    coding_system = Column(String, nullable=True)
    coding_code = Column(String, nullable=True)
    coding_display = Column(String, nullable=True)
    text = Column(String, nullable=True)

    encounter = relationship("EncounterModel", back_populates="diet_preferences")


class EncounterSpecialArrangement(Base):
    """hospitalization.specialArrangement[] (0..*) CodeableConcept."""

    __tablename__ = "encounter_special_arrangement"

    id = Column(Integer, primary_key=True, autoincrement=True)
    encounter_id = Column(
        Integer, ForeignKey("encounter.id"), nullable=False, index=True
    )
    org_id = Column(String, nullable=True)

    coding_system = Column(String, nullable=True)
    coding_code = Column(String, nullable=True)
    coding_display = Column(String, nullable=True)
    text = Column(String, nullable=True)

    encounter = relationship("EncounterModel", back_populates="special_arrangements")


class EncounterSpecialCourtesy(Base):
    """hospitalization.specialCourtesy[] (0..*) CodeableConcept."""

    __tablename__ = "encounter_special_courtesy"

    id = Column(Integer, primary_key=True, autoincrement=True)
    encounter_id = Column(
        Integer, ForeignKey("encounter.id"), nullable=False, index=True
    )
    org_id = Column(String, nullable=True)

    coding_system = Column(String, nullable=True)
    coding_code = Column(String, nullable=True)
    coding_display = Column(String, nullable=True)
    text = Column(String, nullable=True)

    encounter = relationship("EncounterModel", back_populates="special_courtesies")


class EncounterLocation(Base):
    """location[] (0..*) BackboneElement."""

    __tablename__ = "encounter_location"

    id = Column(Integer, primary_key=True, autoincrement=True)
    encounter_id = Column(
        Integer, ForeignKey("encounter.id"), nullable=False, index=True
    )
    org_id = Column(String, nullable=True)

    # location (1..1 Reference(Location))
    reference_type = Column(
        Enum(EncounterLocationReferenceType, name="encounter_location_reference_type"),
        nullable=True,
    )
    reference_id = Column(Integer, nullable=True)
    reference_display = Column(String, nullable=True)

    status = Column(
        Enum(EncounterLocationStatus, name="encounter_location_status"),
        nullable=True,
    )

    # physicalType (0..1 CodeableConcept)
    physical_type_system = Column(String, nullable=True)
    physical_type_code = Column(String, nullable=True)
    physical_type_display = Column(String, nullable=True)
    physical_type_text = Column(String, nullable=True)

    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    encounter = relationship("EncounterModel", back_populates="locations")
