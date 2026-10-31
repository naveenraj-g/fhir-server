from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    Sequence,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.communication_request.enums import (
    CommunicationRequestEncounterReferenceType,
    CommunicationRequestPriority,
    CommunicationRequestRequesterReferenceType,
    CommunicationRequestSenderReferenceType,
    CommunicationRequestStatus,
    CommunicationRequestSubjectReferenceType,
)
from app.models.enums import IdentifierUse, OrganizationReferenceType
from app.models.shared import TenantAuditMixin


class CommunicationRequestModel(TenantAuditMixin, Base):
    """SQLAlchemy ORM model for FHIR R4 CommunicationRequest resource.

    A request to convey information; e.g. the alert, notification, or request to make a phone call.
    Sequenced public ID block starts at 470000 (communication_request_pub_seq).
    There is deliberately no user_id: CommunicationRequest is an org-scoped clinical entity.
    """

    __tablename__ = "communication_request"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    communication_request_id = Column(
        BigInteger,
        Sequence(
            "communication_request_pub_seq",
            start=470000,
            increment=1,
            metadata=Base.metadata,
        ),
        unique=True,
        index=True,
        nullable=False,
    )

    # groupIdentifier (0..1 Identifier)
    group_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False),
        nullable=True,
    )
    group_identifier_system = Column(String, nullable=True)
    group_identifier_value = Column(String, nullable=True)
    group_identifier_period_start = Column(
        DateTime(timezone=True), nullable=True
    )
    group_identifier_period_end = Column(
        DateTime(timezone=True), nullable=True
    )
    group_identifier_assigner_reference = Column(String, nullable=True)
    group_identifier_assigner_type = Column(
        Enum(
            OrganizationReferenceType,
            name="organization_reference_type",
            create_type=False,
        ),
        nullable=True,
    )
    group_identifier_assigner_id = Column(
        BigInteger, nullable=True, index=True
    )
    group_identifier_assigner_display = Column(String, nullable=True)

    # status (1..1 code, binding: request-status)
    status = Column(
        Enum(
            CommunicationRequestStatus,
            name="communication_request_status",
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=False,
    )

    # statusReason (0..1 CodeableConcept) — text stored flat, codings in communication_request_status_reason_coding
    status_reason_text = Column(String, nullable=True)

    # priority (0..1 code, binding: request-priority)
    priority = Column(
        Enum(
            CommunicationRequestPriority,
            name="communication_request_priority",
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=True,
    )

    # doNotPerform (0..1 boolean)
    do_not_perform = Column(Boolean, nullable=True)

    # subject (0..1 Reference(Patient | Group))
    subject_reference = Column(String, nullable=True)
    subject_type = Column(
        Enum(
            CommunicationRequestSubjectReferenceType,
            name="communication_request_subject_reference_type",
        ),
        nullable=True,
    )
    subject_id = Column(BigInteger, nullable=True, index=True)
    subject_display = Column(String, nullable=True)

    # encounter (0..1 Reference(Encounter))
    encounter_reference = Column(String, nullable=True)
    encounter_type = Column(
        Enum(
            CommunicationRequestEncounterReferenceType,
            name="communication_request_encounter_reference_type",
        ),
        nullable=True,
    )
    encounter_id = Column(BigInteger, nullable=True, index=True)
    encounter_display = Column(String, nullable=True)

    # occurrence[x] (0..1 dateTime | Period)
    occurrence_date_time = Column(DateTime(timezone=True), nullable=True)
    occurrence_period_start = Column(DateTime(timezone=True), nullable=True)
    occurrence_period_end = Column(DateTime(timezone=True), nullable=True)

    # authoredOn (0..1 dateTime)
    authored_on = Column(DateTime(timezone=True), nullable=True)

    # requester (0..1 Reference(Practitioner | PractitionerRole | Organization | Patient | RelatedPerson | Device))
    requester_reference = Column(String, nullable=True)
    requester_type = Column(
        Enum(
            CommunicationRequestRequesterReferenceType,
            name="communication_request_requester_reference_type",
        ),
        nullable=True,
    )
    requester_id = Column(BigInteger, nullable=True, index=True)
    requester_display = Column(String, nullable=True)

    # sender (0..1 Reference(Device | Organization | Patient | Practitioner | PractitionerRole | RelatedPerson | HealthcareService))
    sender_reference = Column(String, nullable=True)
    sender_type = Column(
        Enum(
            CommunicationRequestSenderReferenceType,
            name="communication_request_sender_reference_type",
        ),
        nullable=True,
    )
    sender_id = Column(BigInteger, nullable=True, index=True)
    sender_display = Column(String, nullable=True)

    # extension (0..* Extension, JSONB)
    extension = Column(JSONB, nullable=False, server_default=text("'[]'"))

    # Relationships
    identifiers = relationship(
        "CommunicationRequestIdentifier",
        back_populates="communication_request",
        cascade="all, delete-orphan",
    )
    based_on_list = relationship(
        "CommunicationRequestBasedOn",
        back_populates="communication_request",
        cascade="all, delete-orphan",
    )
    replaces_list = relationship(
        "CommunicationRequestReplaces",
        back_populates="communication_request",
        cascade="all, delete-orphan",
    )
    status_reason_codings = relationship(
        "CommunicationRequestStatusReasonCoding",
        back_populates="communication_request",
        cascade="all, delete-orphan",
    )
    categories = relationship(
        "CommunicationRequestCategory",
        back_populates="communication_request",
        cascade="all, delete-orphan",
    )
    medium_list = relationship(
        "CommunicationRequestMedium",
        back_populates="communication_request",
        cascade="all, delete-orphan",
    )
    about_list = relationship(
        "CommunicationRequestAbout",
        back_populates="communication_request",
        cascade="all, delete-orphan",
    )
    payloads = relationship(
        "CommunicationRequestPayload",
        back_populates="communication_request",
        cascade="all, delete-orphan",
    )
    recipients = relationship(
        "CommunicationRequestRecipient",
        back_populates="communication_request",
        cascade="all, delete-orphan",
    )
    reason_codes = relationship(
        "CommunicationRequestReasonCode",
        back_populates="communication_request",
        cascade="all, delete-orphan",
    )
    reason_references = relationship(
        "CommunicationRequestReasonReference",
        back_populates="communication_request",
        cascade="all, delete-orphan",
    )
    notes = relationship(
        "CommunicationRequestNote",
        back_populates="communication_request",
        cascade="all, delete-orphan",
    )
