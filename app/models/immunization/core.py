from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    Numeric,
    Sequence,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.enums import IdentifierUse
from app.models.immunization.enums import (
    ImmunizationEncounterReferenceType,
    ImmunizationLocationReferenceType,
    ImmunizationManufacturerReferenceType,
    ImmunizationPatientReferenceType,
    ImmunizationStatus,
)
from app.models.shared import TenantAuditMixin

_seq = Sequence(
    "immunization_pub_seq",
    start=330000,
    increment=1,
    metadata=Base.metadata,
)


class ImmunizationModel(TenantAuditMixin, Base):
    """FHIR R4 Immunization resource.

    Describes the event of a patient being administered a vaccine or a record
    of an immunization as reported by a patient, a clinician or another party.
    """

    __tablename__ = "immunization"

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    immunization_id = Column(
        BigInteger,
        _seq,
        server_default=_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    # Resource-level extension (0..* Extension)
    extension = Column(JSONB, nullable=False, server_default=text("'[]'"))

    status = Column(
        Enum(
            ImmunizationStatus,
            name="immunization_status",
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=False,
    )

    # statusReason (0..1 CodeableConcept) — text flattened
    status_reason_text = Column(String, nullable=True)

    # vaccineCode (1..1 CodeableConcept) — text flattened
    vaccine_code_text = Column(String, nullable=True)

    # patient (1..1 Reference(Patient))
    patient_reference = Column(String, nullable=False)
    patient_type = Column(
        Enum(
            ImmunizationPatientReferenceType,
            name="immunization_patient_reference_type",
        ),
        nullable=False,
    )
    patient_id = Column(BigInteger, nullable=True, index=True)
    patient_display = Column(String, nullable=True)

    # patient.identifier fallback (11 columns)
    patient_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    patient_identifier_type_system = Column(String, nullable=True)
    patient_identifier_type_version = Column(String, nullable=True)
    patient_identifier_type_code = Column(String, nullable=True)
    patient_identifier_type_display = Column(String, nullable=True)
    patient_identifier_type_user_selected = Column(Boolean, nullable=True)
    patient_identifier_type_text = Column(String, nullable=True)
    patient_identifier_system = Column(String, nullable=True)
    patient_identifier_value = Column(String, nullable=True)
    patient_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    patient_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    # encounter (0..1 Reference(Encounter))
    encounter_reference = Column(String, nullable=True)
    encounter_type = Column(
        Enum(
            ImmunizationEncounterReferenceType,
            name="immunization_encounter_reference_type",
        ),
        nullable=True,
    )
    encounter_id = Column(BigInteger, nullable=True, index=True)
    encounter_display = Column(String, nullable=True)

    # encounter.identifier fallback (11 columns)
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

    # occurrence[x] (1..1 choice: dateTime | string)
    occurrence_date_time = Column(DateTime(timezone=True), nullable=True)
    occurrence_string = Column(String, nullable=True)

    # recorded (0..1 dateTime)
    recorded = Column(DateTime(timezone=True), nullable=True)

    # primarySource (0..1 boolean)
    primary_source = Column(Boolean, nullable=True)

    # reportOrigin (0..1 CodeableConcept) — text flattened
    report_origin_text = Column(String, nullable=True)

    # location (0..1 Reference(Location))
    location_reference = Column(String, nullable=True)
    location_type = Column(
        Enum(
            ImmunizationLocationReferenceType,
            name="immunization_location_reference_type",
        ),
        nullable=True,
    )
    location_id = Column(BigInteger, nullable=True, index=True)
    location_display = Column(String, nullable=True)

    # location.identifier fallback (11 columns)
    location_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    location_identifier_type_system = Column(String, nullable=True)
    location_identifier_type_version = Column(String, nullable=True)
    location_identifier_type_code = Column(String, nullable=True)
    location_identifier_type_display = Column(String, nullable=True)
    location_identifier_type_user_selected = Column(Boolean, nullable=True)
    location_identifier_type_text = Column(String, nullable=True)
    location_identifier_system = Column(String, nullable=True)
    location_identifier_value = Column(String, nullable=True)
    location_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    location_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    # manufacturer (0..1 Reference(Organization))
    manufacturer_reference = Column(String, nullable=True)
    manufacturer_type = Column(
        Enum(
            ImmunizationManufacturerReferenceType,
            name="immunization_manufacturer_reference_type",
        ),
        nullable=True,
    )
    manufacturer_id = Column(BigInteger, nullable=True, index=True)
    manufacturer_display = Column(String, nullable=True)

    # manufacturer.identifier fallback (11 columns)
    manufacturer_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    manufacturer_identifier_type_system = Column(String, nullable=True)
    manufacturer_identifier_type_version = Column(String, nullable=True)
    manufacturer_identifier_type_code = Column(String, nullable=True)
    manufacturer_identifier_type_display = Column(String, nullable=True)
    manufacturer_identifier_type_user_selected = Column(Boolean, nullable=True)
    manufacturer_identifier_type_text = Column(String, nullable=True)
    manufacturer_identifier_system = Column(String, nullable=True)
    manufacturer_identifier_value = Column(String, nullable=True)
    manufacturer_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    manufacturer_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    # lotNumber (0..1 string)
    lot_number = Column(String, nullable=True)

    # expirationDate (0..1 date)
    expiration_date = Column(Date, nullable=True)

    # site (0..1 CodeableConcept) — text flattened
    site_text = Column(String, nullable=True)

    # route (0..1 CodeableConcept) — text flattened
    route_text = Column(String, nullable=True)

    # doseQuantity (0..1 SimpleQuantity) — flattened
    dose_quantity_value = Column(Numeric(18, 4), nullable=True)
    dose_quantity_unit = Column(String, nullable=True)
    dose_quantity_system = Column(String, nullable=True)
    dose_quantity_code = Column(String, nullable=True)

    # isSubpotent (0..1 boolean)
    is_subpotent = Column(Boolean, nullable=True)

    # fundingSource (0..1 CodeableConcept) — text flattened
    funding_source_text = Column(String, nullable=True)

    # Relationships
    identifiers = relationship(
        "ImmunizationIdentifierModel",
        back_populates="immunization",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    status_reason_codings = relationship(
        "ImmunizationStatusReasonCodingModel",
        back_populates="immunization",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    vaccine_codings = relationship(
        "ImmunizationVaccineCodingModel",
        back_populates="immunization",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    report_origin_codings = relationship(
        "ImmunizationReportOriginCodingModel",
        back_populates="immunization",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    site_codings = relationship(
        "ImmunizationSiteCodingModel",
        back_populates="immunization",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    route_codings = relationship(
        "ImmunizationRouteCodingModel",
        back_populates="immunization",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    funding_source_codings = relationship(
        "ImmunizationFundingSourceCodingModel",
        back_populates="immunization",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    performers = relationship(
        "ImmunizationPerformerModel",
        back_populates="immunization",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    notes = relationship(
        "ImmunizationNoteModel",
        back_populates="immunization",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    reason_codes = relationship(
        "ImmunizationReasonCodeModel",
        back_populates="immunization",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    reason_references = relationship(
        "ImmunizationReasonReferenceModel",
        back_populates="immunization",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    subpotent_reasons = relationship(
        "ImmunizationSubpotentReasonModel",
        back_populates="immunization",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    education_items = relationship(
        "ImmunizationEducationModel",
        back_populates="immunization",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    program_eligibilities = relationship(
        "ImmunizationProgramEligibilityModel",
        back_populates="immunization",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    reactions = relationship(
        "ImmunizationReactionModel",
        back_populates="immunization",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    protocol_applied_items = relationship(
        "ImmunizationProtocolAppliedModel",
        back_populates="immunization",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
