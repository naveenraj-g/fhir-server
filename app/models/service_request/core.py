from sqlalchemy import BigInteger, Column, DateTime, Enum, Index, Sequence, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin

from .enums import ServiceRequestIntent, ServiceRequestPriority, ServiceRequestStatus

service_request_id_seq = Sequence(
    "service_request_pub_seq", start=80000, increment=1, metadata=Base.metadata
)

# R4 targets of ServiceRequest.subject and ServiceRequest.requester.
SUBJECT_TYPES = ("Patient", "Group", "Location", "Device")
REQUESTER_TYPES = (
    "Practitioner",
    "PractitionerRole",
    "Organization",
    "Patient",
    "RelatedPerson",
    "Device",
)


def _enum(cls, name):
    # Stored by value, so `on-hold` / `original-order` are the real FHIR codes.
    return Enum(cls, name=name, values_callable=lambda e: [m.value for m in e])


class ServiceRequestModel(TenantAuditMixin, Base):
    """FHIR R4 ServiceRequest - Medplum-style storage, same as Patient, Encounter,
    Condition, Procedure and the other content-based resources.

    `content` (JSONB) holds the whole resource exactly as validated on write; it is
    the single source of truth, and GET serves it back as-is (`id`/`meta` are stamped
    on at read time from this row's own columns - see app.fhir.mappers.service_request).
    Nothing else in this table or its child tables is a second copy of the resource:
    every other column exists only because a FHIR R4 ServiceRequest search parameter
    filters on it (https://www.hl7.org/fhir/R4/servicerequest.html#search), and is
    derived from `content` on every write by app.repository.service_request._indexer.

    Search parameter -> storage:
      status, intent, priority
                       -> Enum columns (stored by value, so `on-hold` and
                          `original-order` are the real FHIR codes)
      authored         -> authored_start/_end (authoredOn, the range the dateTime covers)
      occurrence       -> occurrence_start/_end (occurrence[x] as a dateTime, a Period or a
                          Timing: the half-open range it covers, NULL = open)
      requisition      -> requisition_system/_value (0..1 Identifier, columns)
      subject, patient -> subject_reference/_type/_id + subject_identifier_*
                          (1..1 Reference(Patient | Group | Location | Device); `patient`
                          is the same columns narrowed to Patient)
      encounter        -> encounter_reference/_type/_id + encounter_identifier_*
      requester        -> requester_reference/_type/_id + requester_identifier_*
                          (0..1 Reference of six types)
      identifier       -> ServiceRequestIdentifier (0..*)
      category, code, body-site, performer-type
                       -> ServiceRequestToken (one shared table)
      based-on, replaces, specimen, instantiates-canonical
                       -> ServiceRequestReference (one shared table)
      performer        -> ServiceRequestPerformer (one row per performer reference)
      instantiates-uri -> ServiceRequestInstantiatesUri (one row per URI)
      _id              -> service_request_id;  _lastUpdated -> updated_at/created_at

    `doNotPerform`, `orderDetail`, `quantity[x]`, `asNeeded[x]`, `locationCode`,
    `locationReference`, `reasonCode`, `reasonReference`, `insurance`, `supportingInfo`,
    `note`, `patientInstruction`, `relevantHistory` and `extension` have no search
    parameter and live only in `content`.

    `subject`, `requester`, `performer` and the reference-table parameters can point at
    several resource types, so `*_type` records which one a relative `Type/<id>` names
    (a plain string, not a Postgres enum): a search by bare id is ambiguous for them
    (`subject=Type/id` or `subject:Type=id`; `encounter`, `replaces` and `specimen`
    have one target so a bare id works).

    All index columns are nullable: R4 makes `status`, `intent` and `subject` mandatory,
    but that is the validator's rule (enforced by the `java_validator` backend), not the
    database's. No `user_id`: a ServiceRequest is a shared tenant-level entity. No
    DB-level CHECK constraints."""

    __tablename__ = "service_request"
    __table_args__ = (
        Index("ix_service_request_authored", "authored_start", "authored_end"),
        Index("ix_service_request_occurrence", "occurrence_start", "occurrence_end"),
        Index("ix_service_request_subject_type_id", "subject_type", "subject_id"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    service_request_id = Column(
        BigInteger,
        service_request_id_seq,
        server_default=service_request_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    # The whole FHIR resource minus resourceType/id/meta (server-stamped).
    content = Column(JSONB, nullable=False)

    # -- Search index (derived from `content`) --
    status = Column(
        _enum(ServiceRequestStatus, "service_request_status"), nullable=True
    )
    intent = Column(
        _enum(ServiceRequestIntent, "service_request_intent"), nullable=True
    )
    priority = Column(
        _enum(ServiceRequestPriority, "service_request_priority"), nullable=True
    )

    # authoredOn and occurrence[x]: the half-open [start, end) range of instants each
    # covers (NULL = open / absent), matched with period_match.
    authored_start = Column(DateTime(timezone=True), nullable=True)
    authored_end = Column(DateTime(timezone=True), nullable=True)
    occurrence_start = Column(DateTime(timezone=True), nullable=True)
    occurrence_end = Column(DateTime(timezone=True), nullable=True)

    # requisition (0..1 Identifier)
    requisition_system = Column(String, nullable=True)
    requisition_value = Column(String, nullable=True)

    # subject (1..1 Reference(Patient | Group | Location | Device))
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

    # requester (0..1 Reference(Practitioner | PractitionerRole | Organization | Patient |
    # RelatedPerson | Device))
    requester_reference = Column(String, nullable=True)
    requester_type = Column(String, nullable=True)
    requester_id = Column(BigInteger, nullable=True, index=True)
    requester_identifier_system = Column(String, nullable=True)
    requester_identifier_value = Column(String, nullable=True)

    identifiers = relationship(
        "ServiceRequestIdentifier",
        back_populates="service_request",
        cascade="all, delete-orphan",
    )
    tokens = relationship(
        "ServiceRequestToken",
        back_populates="service_request",
        cascade="all, delete-orphan",
    )
    references = relationship(
        "ServiceRequestReference",
        back_populates="service_request",
        cascade="all, delete-orphan",
    )
    performers = relationship(
        "ServiceRequestPerformer",
        back_populates="service_request",
        cascade="all, delete-orphan",
    )
    instantiates_uris = relationship(
        "ServiceRequestInstantiatesUri",
        back_populates="service_request",
        cascade="all, delete-orphan",
    )
