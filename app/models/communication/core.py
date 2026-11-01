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
from app.models.communication.enums import (
    CommunicationEncounterReferenceType,
    CommunicationPriority,
    CommunicationSenderReferenceType,
    CommunicationStatus,
    CommunicationSubjectReferenceType,
)
from app.models.shared import TenantAuditMixin


class CommunicationModel(TenantAuditMixin, Base):
    """SQLAlchemy ORM model for FHIR R4 Communication resource.

    An occurrence of information being transmitted; e.g. an alert that was sent to a
    responsible provider, a public health agency that was notified about a reportable condition.
    Sequenced public ID block starts at 480000 (communication_pub_seq).
    There is deliberately no user_id: Communication is an org-scoped clinical entity.
    """

    __tablename__ = "communication"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    communication_id = Column(
        BigInteger,
        Sequence(
            "communication_pub_seq",
            start=480000,
            increment=1,
            metadata=Base.metadata,
        ),
        unique=True,
        index=True,
        nullable=False,
    )

    # instantiatesCanonical (0..* canonical)
    instantiates_canonical = Column(ARRAY(String), nullable=True)

    # instantiatesUri (0..* uri)
    instantiates_uri = Column(ARRAY(String), nullable=True)

    # status (1..1 code, binding: event-status)
    status = Column(
        Enum(
            CommunicationStatus,
            name="communication_status",
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=False,
    )

    # statusReason (0..1 CodeableConcept) — text stored flat, codings in communication_status_reason_coding
    status_reason_text = Column(String, nullable=True)

    # priority (0..1 code, binding: request-priority)
    priority = Column(
        Enum(
            CommunicationPriority,
            name="communication_priority",
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=True,
    )

    # subject (0..1 Reference(Patient | Group))
    subject_reference = Column(String, nullable=True)
    subject_type = Column(
        Enum(
            CommunicationSubjectReferenceType,
            name="communication_subject_reference_type",
        ),
        nullable=True,
    )
    subject_id = Column(BigInteger, nullable=True, index=True)
    subject_display = Column(String, nullable=True)

    # topic (0..1 CodeableConcept) — text stored flat, codings in communication_topic_coding
    topic_text = Column(String, nullable=True)

    # encounter (0..1 Reference(Encounter))
    encounter_reference = Column(String, nullable=True)
    encounter_type = Column(
        Enum(
            CommunicationEncounterReferenceType,
            name="communication_encounter_reference_type",
        ),
        nullable=True,
    )
    encounter_id = Column(BigInteger, nullable=True, index=True)
    encounter_display = Column(String, nullable=True)

    # sent (0..1 dateTime)
    sent = Column(DateTime(timezone=True), nullable=True)

    # received (0..1 dateTime)
    received = Column(DateTime(timezone=True), nullable=True)

    # sender (0..1 Reference(Device | Organization | Patient | Practitioner | PractitionerRole | RelatedPerson | HealthcareService))
    sender_reference = Column(String, nullable=True)
    sender_type = Column(
        Enum(
            CommunicationSenderReferenceType,
            name="communication_sender_reference_type",
        ),
        nullable=True,
    )
    sender_id = Column(BigInteger, nullable=True, index=True)
    sender_display = Column(String, nullable=True)

    # extension (0..* Extension, JSONB)
    extension = Column(JSONB, nullable=False, server_default=text("'[]'"))

    # Relationships
    identifiers = relationship(
        "CommunicationIdentifier",
        back_populates="communication",
        cascade="all, delete-orphan",
    )
    based_on_list = relationship(
        "CommunicationBasedOn",
        back_populates="communication",
        cascade="all, delete-orphan",
    )
    part_of_list = relationship(
        "CommunicationPartOf",
        back_populates="communication",
        cascade="all, delete-orphan",
    )
    in_response_to_list = relationship(
        "CommunicationInResponseTo",
        back_populates="communication",
        cascade="all, delete-orphan",
    )
    status_reason_codings = relationship(
        "CommunicationStatusReasonCoding",
        back_populates="communication",
        cascade="all, delete-orphan",
    )
    categories = relationship(
        "CommunicationCategory",
        back_populates="communication",
        cascade="all, delete-orphan",
    )
    medium_list = relationship(
        "CommunicationMedium",
        back_populates="communication",
        cascade="all, delete-orphan",
    )
    topic_codings = relationship(
        "CommunicationTopicCoding",
        back_populates="communication",
        cascade="all, delete-orphan",
    )
    about_list = relationship(
        "CommunicationAbout",
        back_populates="communication",
        cascade="all, delete-orphan",
    )
    recipients = relationship(
        "CommunicationRecipient",
        back_populates="communication",
        cascade="all, delete-orphan",
    )
    reason_codes = relationship(
        "CommunicationReasonCode",
        back_populates="communication",
        cascade="all, delete-orphan",
    )
    reason_references = relationship(
        "CommunicationReasonReference",
        back_populates="communication",
        cascade="all, delete-orphan",
    )
    payloads = relationship(
        "CommunicationPayload",
        back_populates="communication",
        cascade="all, delete-orphan",
    )
    notes = relationship(
        "CommunicationNote",
        back_populates="communication",
        cascade="all, delete-orphan",
    )
