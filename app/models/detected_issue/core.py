from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    Sequence,
    String,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.enums import IdentifierUse
from app.models.shared import TenantAuditMixin

from .enums import (
    DetectedIssueAuthorReferenceType,
    DetectedIssuePatientReferenceType,
    DetectedIssueSeverity,
    DetectedIssueStatus,
)

detected_issue_pub_seq = Sequence(
    "detected_issue_pub_seq", start=540000, increment=1, metadata=Base.metadata
)


class DetectedIssueModel(TenantAuditMixin, Base):
    """FHIR R4 DetectedIssue resource model."""

    __tablename__ = "detected_issue"

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    detected_issue_id = Column(
        BigInteger,
        detected_issue_pub_seq,
        server_default=detected_issue_pub_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    # status (1..1 code)
    status = Column(
        Enum(
            DetectedIssueStatus,
            name="detected_issue_status",
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=False,
    )

    # code (0..1 CodeableConcept)
    code_text = Column(String, nullable=True)

    # severity (0..1 code)
    severity = Column(
        Enum(
            DetectedIssueSeverity,
            name="detected_issue_severity",
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=True,
    )

    # patient (0..1 Reference(Patient))
    patient_reference = Column(String, nullable=True)
    patient_type = Column(
        Enum(
            DetectedIssuePatientReferenceType,
            name="detected_issue_patient_reference_type",
        ),
        nullable=True,
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

    # identified[x] (0..1 dateTime | Period)
    identified_date_time = Column(DateTime(timezone=True), nullable=True)
    identified_period_start = Column(DateTime(timezone=True), nullable=True)
    identified_period_end = Column(DateTime(timezone=True), nullable=True)

    # author (0..1 Reference(Practitioner | PractitionerRole | Device))
    author_reference = Column(String, nullable=True)
    author_type = Column(
        Enum(
            DetectedIssueAuthorReferenceType,
            name="detected_issue_author_reference_type",
        ),
        nullable=True,
    )
    author_id = Column(BigInteger, nullable=True, index=True)
    author_display = Column(String, nullable=True)

    # author.identifier fallback (11 columns)
    author_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    author_identifier_type_system = Column(String, nullable=True)
    author_identifier_type_version = Column(String, nullable=True)
    author_identifier_type_code = Column(String, nullable=True)
    author_identifier_type_display = Column(String, nullable=True)
    author_identifier_type_user_selected = Column(Boolean, nullable=True)
    author_identifier_type_text = Column(String, nullable=True)
    author_identifier_system = Column(String, nullable=True)
    author_identifier_value = Column(String, nullable=True)
    author_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    author_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    # detail (0..1 string)
    detail = Column(String, nullable=True)

    # reference (0..1 uri)
    reference = Column(String, nullable=True)

    # extension (DomainResource extension)
    extension = Column(JSONB, nullable=True)

    # Relationships
    identifiers = relationship(
        "DetectedIssueIdentifierModel",
        back_populates="detected_issue",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    code_codings = relationship(
        "DetectedIssueCodeCodingModel",
        back_populates="detected_issue",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    implicated_resources = relationship(
        "DetectedIssueImplicatedModel",
        back_populates="detected_issue",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    evidence_list = relationship(
        "DetectedIssueEvidenceModel",
        back_populates="detected_issue",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    mitigations = relationship(
        "DetectedIssueMitigationModel",
        back_populates="detected_issue",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
