from sqlalchemy import BigInteger, Column, Enum, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.communication_request.enums import (
    CommunicationRequestReasonReferenceType,
    CommunicationRequestRecipientReferenceType,
)
from app.models.shared import TenantAuditMixin


class CommunicationRequestBasedOn(TenantAuditMixin, Base):
    """CommunicationRequest.basedOn (0..*) child table. Reference(Resource)."""

    __tablename__ = "communication_request_based_on"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    communication_request_pk = Column(
        BigInteger,
        ForeignKey("communication_request.id"),
        nullable=False,
        index=True,
    )

    reference_reference = Column(String, nullable=True)
    reference_type = Column(String, nullable=True)
    reference_id = Column(BigInteger, nullable=True, index=True)
    reference_display = Column(String, nullable=True)

    communication_request = relationship(
        "CommunicationRequestModel", back_populates="based_on_list"
    )


class CommunicationRequestReplaces(TenantAuditMixin, Base):
    """CommunicationRequest.replaces (0..*) child table. Reference(CommunicationRequest)."""

    __tablename__ = "communication_request_replaces"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    communication_request_pk = Column(
        BigInteger,
        ForeignKey("communication_request.id"),
        nullable=False,
        index=True,
    )

    reference_reference = Column(String, nullable=True)
    reference_type = Column(String, nullable=True)
    reference_id = Column(BigInteger, nullable=True, index=True)
    reference_display = Column(String, nullable=True)

    communication_request = relationship(
        "CommunicationRequestModel", back_populates="replaces_list"
    )


class CommunicationRequestAbout(TenantAuditMixin, Base):
    """CommunicationRequest.about (0..*) child table. Reference(Resource)."""

    __tablename__ = "communication_request_about"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    communication_request_pk = Column(
        BigInteger,
        ForeignKey("communication_request.id"),
        nullable=False,
        index=True,
    )

    reference_reference = Column(String, nullable=True)
    reference_type = Column(String, nullable=True)
    reference_id = Column(BigInteger, nullable=True, index=True)
    reference_display = Column(String, nullable=True)

    communication_request = relationship(
        "CommunicationRequestModel", back_populates="about_list"
    )


class CommunicationRequestRecipient(TenantAuditMixin, Base):
    """CommunicationRequest.recipient (0..*) child table. Reference(Device|Organization|Patient|Practitioner|PractitionerRole|RelatedPerson|Group|CareTeam|HealthcareService)."""

    __tablename__ = "communication_request_recipient"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    communication_request_pk = Column(
        BigInteger,
        ForeignKey("communication_request.id"),
        nullable=False,
        index=True,
    )

    reference_reference = Column(String, nullable=True)
    reference_type = Column(
        Enum(
            CommunicationRequestRecipientReferenceType,
            name="communication_request_recipient_reference_type",
        ),
        nullable=True,
    )
    reference_id = Column(BigInteger, nullable=True, index=True)
    reference_display = Column(String, nullable=True)

    communication_request = relationship(
        "CommunicationRequestModel", back_populates="recipients"
    )


class CommunicationRequestReasonReference(TenantAuditMixin, Base):
    """CommunicationRequest.reasonReference (0..*) child table. Reference(Condition|Observation|DiagnosticReport|DocumentReference)."""

    __tablename__ = "communication_request_reason_reference"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    communication_request_pk = Column(
        BigInteger,
        ForeignKey("communication_request.id"),
        nullable=False,
        index=True,
    )

    reference_reference = Column(String, nullable=True)
    reference_type = Column(
        Enum(
            CommunicationRequestReasonReferenceType,
            name="communication_request_reason_reference_type",
        ),
        nullable=True,
    )
    reference_id = Column(BigInteger, nullable=True, index=True)
    reference_display = Column(String, nullable=True)

    communication_request = relationship(
        "CommunicationRequestModel", back_populates="reason_references"
    )
