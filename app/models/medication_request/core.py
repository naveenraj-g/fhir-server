from sqlalchemy import BigInteger, Column, DateTime, Enum, Index, Sequence, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin

from .enums import (
    MedicationRequestIntent,
    MedicationRequestPriority,
    MedicationRequestStatus,
)

medication_request_id_seq = Sequence(
    "medication_request_pub_seq", start=90000, increment=1, metadata=Base.metadata
)

# R4 targets of the 0..1 references that are searched.
SUBJECT_TYPES = ("Patient", "Group")
MEDICATION_TYPES = ("Medication",)
REQUESTER_TYPES = (
    "Practitioner",
    "PractitionerRole",
    "Organization",
    "Patient",
    "RelatedPerson",
    "Device",
)
PERFORMER_TYPES = (
    "Practitioner",
    "PractitionerRole",
    "Organization",
    "Patient",
    "Device",
    "RelatedPerson",
    "CareTeam",
)
DISPENSER_TYPES = ("Organization",)


def _enum(cls, name):
    # Stored by value, so `on-hold` / `original-order` are the real FHIR codes.
    return Enum(cls, name=name, values_callable=lambda e: [m.value for m in e])


class MedicationRequestModel(TenantAuditMixin, Base):
    """FHIR R4 MedicationRequest - Medplum-style storage, same as Patient, Encounter,
    Condition, Procedure, ServiceRequest, Medication and the other content-based resources.

    `content` (JSONB) holds the whole resource exactly as validated on write; it is the
    single source of truth, and GET serves it back as-is (`id`/`meta` are stamped on at read
    time from this row's own columns - see app.fhir.mappers.medication_request). Nothing
    else in this table or its child tables is a second copy of the resource: every other
    column exists only because a FHIR R4 MedicationRequest search parameter filters on it
    (https://www.hl7.org/fhir/R4/medicationrequest.html#search), and is derived from
    `content` on every write by app.repository.medication_request._indexer.

    Search parameter -> storage:
      status, intent, priority
                       -> Enum columns (stored by value, so `on-hold` and `original-order`
                          are the real FHIR codes)
      authoredon       -> authored_start/_end (authoredOn, the range the dateTime covers)
      subject, patient -> subject_reference/_type/_id + subject_identifier_*
                          (1..1 Reference(Patient | Group); `patient` is the same columns
                          narrowed to Patient)
      encounter        -> encounter_reference/_type/_id + encounter_identifier_*
      requester        -> requester_reference/_type/_id + requester_identifier_*
      intended-performer
                       -> performer_reference/_type/_id + performer_identifier_*
                          (0..1 Reference of seven types)
      medication       -> medication_reference/_type/_id + medication_identifier_*
                          (medication[x] as a Reference(Medication); a medicationCodeableConcept
                          leaves these NULL)
      intended-dispenser
                       -> dispenser_reference/_type/_id + dispenser_identifier_*
                          (dispenseRequest.performer, Reference(Organization))
      identifier       -> MedicationRequestIdentifier (0..*)
      category, code, intended-performertype
                       -> MedicationRequestToken (one shared table; `code` reads
                          medicationCodeableConcept)
      date             -> MedicationRequestTiming (one row per
                          dosageInstruction.timing.event, as the range each dateTime covers)
      _id              -> medication_request_id;  _lastUpdated -> updated_at/created_at

    `statusReason`, `doNotPerform`, `reported[x]`, `supportingInformation`, `recorder`,
    `reasonCode`, `reasonReference`, `instantiatesCanonical`, `instantiatesUri`, `basedOn`,
    `groupIdentifier`, `courseOfTherapyType`, `insurance`, `note`, `dosageInstruction` (apart
    from its timing events), `dispenseRequest` (apart from `performer`), `substitution`,
    `priorPrescription`, `detectedIssue`, `eventHistory` and `extension` have no search
    parameter and live only in `content`.

    `subject`, `requester` and `performer` can point at several resource types, so `*_type`
    records which one a relative `Type/<id>` names (a plain string, not a Postgres enum): a
    search by bare id is ambiguous for them (`subject=Type/id` or `subject:Type=id`;
    `encounter`, `medication` and `intended-dispenser` have one target so a bare id works).

    All index columns are nullable: R4 makes `status`, `intent`, `medication[x]` and `subject`
    mandatory, but that is the validator's rule (enforced by the `java_validator` backend),
    not the database's. No `user_id`: a MedicationRequest is a shared tenant-level entity. No
    DB-level CHECK constraints."""

    __tablename__ = "medication_request"
    __table_args__ = (
        Index("ix_medication_request_authored", "authored_start", "authored_end"),
        Index("ix_medication_request_subject_type_id", "subject_type", "subject_id"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    medication_request_id = Column(
        BigInteger,
        medication_request_id_seq,
        server_default=medication_request_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    # The whole FHIR resource minus resourceType/id/meta (server-stamped).
    content = Column(JSONB, nullable=False)

    # -- Search index (derived from `content`) --
    status = Column(
        _enum(MedicationRequestStatus, "medication_request_status"), nullable=True
    )
    intent = Column(
        _enum(MedicationRequestIntent, "medication_request_intent"), nullable=True
    )
    priority = Column(
        _enum(MedicationRequestPriority, "medication_request_priority"), nullable=True
    )

    # authoredOn: the half-open [start, end) range of instants the dateTime covers.
    authored_start = Column(DateTime(timezone=True), nullable=True)
    authored_end = Column(DateTime(timezone=True), nullable=True)

    # subject (1..1 Reference(Patient | Group))
    subject_reference = Column(String, nullable=True)
    subject_type = Column(String, nullable=True)
    subject_id = Column(BigInteger, nullable=True)
    subject_identifier_system = Column(String, nullable=True)
    subject_identifier_value = Column(String, nullable=True)

    # encounter (0..1 Reference(Encounter))
    encounter_reference = Column(String, nullable=True)
    encounter_type = Column(String, nullable=True)
    encounter_id = Column(BigInteger, nullable=True, index=True)
    encounter_identifier_system = Column(String, nullable=True)
    encounter_identifier_value = Column(String, nullable=True)

    # requester (0..1 Reference of six types)
    requester_reference = Column(String, nullable=True)
    requester_type = Column(String, nullable=True)
    requester_id = Column(BigInteger, nullable=True, index=True)
    requester_identifier_system = Column(String, nullable=True)
    requester_identifier_value = Column(String, nullable=True)

    # performer (0..1 Reference of seven types), searched as `intended-performer`
    performer_reference = Column(String, nullable=True)
    performer_type = Column(String, nullable=True)
    performer_id = Column(BigInteger, nullable=True, index=True)
    performer_identifier_system = Column(String, nullable=True)
    performer_identifier_value = Column(String, nullable=True)

    # medication[x] as a Reference(Medication)
    medication_reference = Column(String, nullable=True)
    medication_type = Column(String, nullable=True)
    medication_id = Column(BigInteger, nullable=True, index=True)
    medication_identifier_system = Column(String, nullable=True)
    medication_identifier_value = Column(String, nullable=True)

    # dispenseRequest.performer (0..1 Reference(Organization)), searched as `intended-dispenser`
    dispenser_reference = Column(String, nullable=True)
    dispenser_type = Column(String, nullable=True)
    dispenser_id = Column(BigInteger, nullable=True, index=True)
    dispenser_identifier_system = Column(String, nullable=True)
    dispenser_identifier_value = Column(String, nullable=True)

    identifiers = relationship(
        "MedicationRequestIdentifier",
        back_populates="medication_request",
        cascade="all, delete-orphan",
    )
    tokens = relationship(
        "MedicationRequestToken",
        back_populates="medication_request",
        cascade="all, delete-orphan",
    )
    timings = relationship(
        "MedicationRequestTiming",
        back_populates="medication_request",
        cascade="all, delete-orphan",
    )
