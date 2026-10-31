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
from app.models.enums import EncounterReferenceType, LocationReferenceType
from app.models.procedure.enums import (
    ProcedureAsserterReferenceType,
    ProcedureRecorderReferenceType,
    ProcedureStatus,
    ProcedureSubjectReferenceType,
)
from app.models.shared import TenantAuditMixin

procedure_pub_seq = Sequence(
    "procedure_pub_seq", start=100000, increment=1, metadata=Base.metadata
)


class ProcedureModel(TenantAuditMixin, Base):
    """Procedure resource model (FHIR R4)."""

    __tablename__ = "procedure"

    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        index=True,
    )
    procedure_id = Column(
        BigInteger,
        procedure_pub_seq,
        server_default=procedure_pub_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )


    extension = Column(JSONB, nullable=False, server_default=text("'[]'"))

    instantiates_canonical = Column(ARRAY(String), nullable=True)
    instantiates_uri = Column(ARRAY(String), nullable=True)

    status = Column(
        Enum(ProcedureStatus, name="procedure_status"),
        nullable=False,
    )

    # statusReason (0..1 CodeableConcept)
    status_reason_text = Column(String, nullable=True)

    # category (0..1 CodeableConcept)
    category_text = Column(String, nullable=True)

    # code (0..1 CodeableConcept)
    code_text = Column(String, nullable=True)

    # subject (1..1 Reference(Patient | Group))
    subject_reference = Column(String, nullable=False)
    subject_type = Column(
        Enum(
            ProcedureSubjectReferenceType,
            name="procedure_subject_reference_type",
        ),
        nullable=False,
    )
    subject_id = Column(BigInteger, nullable=True, index=True)
    subject_display = Column(String, nullable=True)

    # encounter (0..1 Reference(Encounter))
    encounter_reference = Column(String, nullable=True)
    encounter_type = Column(
        Enum(
            EncounterReferenceType,
            name="encounter_reference_type",
            create_type=False,
        ),
        nullable=True,
    )
    encounter_id = Column(BigInteger, nullable=True, index=True)
    encounter_display = Column(String, nullable=True)

    # performed[x] (0..1 dateTime | Period | string | Age | Range)
    performed_date_time = Column(DateTime(timezone=True), nullable=True)
    performed_period_start = Column(DateTime(timezone=True), nullable=True)
    performed_period_end = Column(DateTime(timezone=True), nullable=True)
    performed_string = Column(String, nullable=True)
    performed_age = Column(JSONB, nullable=True)
    performed_range = Column(JSONB, nullable=True)

    # recorder (0..1 Reference(Patient | RelatedPerson | Practitioner | PractitionerRole))
    recorder_reference = Column(String, nullable=True)
    recorder_type = Column(
        Enum(
            ProcedureRecorderReferenceType,
            name="procedure_recorder_reference_type",
        ),
        nullable=True,
    )
    recorder_id = Column(BigInteger, nullable=True, index=True)
    recorder_display = Column(String, nullable=True)

    # asserter (0..1 Reference(Patient | RelatedPerson | Practitioner | PractitionerRole))
    asserter_reference = Column(String, nullable=True)
    asserter_type = Column(
        Enum(
            ProcedureAsserterReferenceType,
            name="procedure_asserter_reference_type",
        ),
        nullable=True,
    )
    asserter_id = Column(BigInteger, nullable=True, index=True)
    asserter_display = Column(String, nullable=True)

    # location (0..1 Reference(Location))
    location_reference = Column(String, nullable=True)
    location_type = Column(
        Enum(
            LocationReferenceType,
            name="location_reference_type",
            create_type=False,
        ),
        nullable=True,
    )
    location_id = Column(BigInteger, nullable=True, index=True)
    location_display = Column(String, nullable=True)

    # outcome (0..1 CodeableConcept)
    outcome_text = Column(String, nullable=True)

    # Relationships
    identifiers = relationship(
        "ProcedureIdentifier",
        back_populates="procedure",
        cascade="all, delete-orphan",
    )
    based_on = relationship(
        "ProcedureBasedOn",
        back_populates="procedure",
        cascade="all, delete-orphan",
    )
    part_of = relationship(
        "ProcedurePartOf",
        back_populates="procedure",
        cascade="all, delete-orphan",
    )
    status_reason_codings = relationship(
        "ProcedureStatusReasonCoding",
        back_populates="procedure",
        cascade="all, delete-orphan",
    )
    category_codings = relationship(
        "ProcedureCategoryCoding",
        back_populates="procedure",
        cascade="all, delete-orphan",
    )
    code_codings = relationship(
        "ProcedureCodeCoding",
        back_populates="procedure",
        cascade="all, delete-orphan",
    )
    performers = relationship(
        "ProcedurePerformer",
        back_populates="procedure",
        cascade="all, delete-orphan",
    )
    reason_codes = relationship(
        "ProcedureReasonCode",
        back_populates="procedure",
        cascade="all, delete-orphan",
    )
    reason_references = relationship(
        "ProcedureReasonReference",
        back_populates="procedure",
        cascade="all, delete-orphan",
    )
    body_sites = relationship(
        "ProcedureBodySite",
        back_populates="procedure",
        cascade="all, delete-orphan",
    )
    outcome_codings = relationship(
        "ProcedureOutcomeCoding",
        back_populates="procedure",
        cascade="all, delete-orphan",
    )
    reports = relationship(
        "ProcedureReport",
        back_populates="procedure",
        cascade="all, delete-orphan",
    )
    complications = relationship(
        "ProcedureComplication",
        back_populates="procedure",
        cascade="all, delete-orphan",
    )
    complication_details = relationship(
        "ProcedureComplicationDetail",
        back_populates="procedure",
        cascade="all, delete-orphan",
    )
    follow_ups = relationship(
        "ProcedureFollowUp",
        back_populates="procedure",
        cascade="all, delete-orphan",
    )
    notes = relationship(
        "ProcedureNote",
        back_populates="procedure",
        cascade="all, delete-orphan",
    )
    focal_devices = relationship(
        "ProcedureFocalDevice",
        back_populates="procedure",
        cascade="all, delete-orphan",
    )
    used_references = relationship(
        "ProcedureUsedReference",
        back_populates="procedure",
        cascade="all, delete-orphan",
    )
    used_codes = relationship(
        "ProcedureUsedCode",
        back_populates="procedure",
        cascade="all, delete-orphan",
    )
