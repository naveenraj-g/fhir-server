from sqlalchemy import BigInteger, Boolean, Column, DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.communication_request.enums import (
    CommunicationRequestReasonReferenceType,
    CommunicationRequestRecipientReferenceType,
)
from app.models.enums import IdentifierUse
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

    # Reference.identifier fallback
    reference_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False),
        nullable=True,
    )
    reference_identifier_type_system = Column(String, nullable=True)
    reference_identifier_type_version = Column(String, nullable=True)
    reference_identifier_type_code = Column(String, nullable=True)
    reference_identifier_type_display = Column(String, nullable=True)
    reference_identifier_type_text = Column(String, nullable=True)
    reference_identifier_type_user_selected = Column(Boolean, nullable=True)
    reference_identifier_system = Column(String, nullable=True)
    reference_identifier_value = Column(String, nullable=True)
    reference_identifier_period_start = Column(
        DateTime(timezone=True), nullable=True
    )
    reference_identifier_period_end = Column(
        DateTime(timezone=True), nullable=True
    )

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

    # Reference.identifier fallback
    reference_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False),
        nullable=True,
    )
    reference_identifier_type_system = Column(String, nullable=True)
    reference_identifier_type_version = Column(String, nullable=True)
    reference_identifier_type_code = Column(String, nullable=True)
    reference_identifier_type_display = Column(String, nullable=True)
    reference_identifier_type_text = Column(String, nullable=True)
    reference_identifier_type_user_selected = Column(Boolean, nullable=True)
    reference_identifier_system = Column(String, nullable=True)
    reference_identifier_value = Column(String, nullable=True)
    reference_identifier_period_start = Column(
        DateTime(timezone=True), nullable=True
    )
    reference_identifier_period_end = Column(
        DateTime(timezone=True), nullable=True
    )

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

    # Reference.identifier fallback
    reference_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False),
        nullable=True,
    )
    reference_identifier_type_system = Column(String, nullable=True)
    reference_identifier_type_version = Column(String, nullable=True)
    reference_identifier_type_code = Column(String, nullable=True)
    reference_identifier_type_display = Column(String, nullable=True)
    reference_identifier_type_text = Column(String, nullable=True)
    reference_identifier_type_user_selected = Column(Boolean, nullable=True)
    reference_identifier_system = Column(String, nullable=True)
    reference_identifier_value = Column(String, nullable=True)
    reference_identifier_period_start = Column(
        DateTime(timezone=True), nullable=True
    )
    reference_identifier_period_end = Column(
        DateTime(timezone=True), nullable=True
    )

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

    # Reference.identifier fallback
    reference_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False),
        nullable=True,
    )
    reference_identifier_type_system = Column(String, nullable=True)
    reference_identifier_type_version = Column(String, nullable=True)
    reference_identifier_type_code = Column(String, nullable=True)
    reference_identifier_type_display = Column(String, nullable=True)
    reference_identifier_type_text = Column(String, nullable=True)
    reference_identifier_type_user_selected = Column(Boolean, nullable=True)
    reference_identifier_system = Column(String, nullable=True)
    reference_identifier_value = Column(String, nullable=True)
    reference_identifier_period_start = Column(
        DateTime(timezone=True), nullable=True
    )
    reference_identifier_period_end = Column(
        DateTime(timezone=True), nullable=True
    )

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

    # Reference.identifier fallback
    reference_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False),
        nullable=True,
    )
    reference_identifier_type_system = Column(String, nullable=True)
    reference_identifier_type_version = Column(String, nullable=True)
    reference_identifier_type_code = Column(String, nullable=True)
    reference_identifier_type_display = Column(String, nullable=True)
    reference_identifier_type_text = Column(String, nullable=True)
    reference_identifier_type_user_selected = Column(Boolean, nullable=True)
    reference_identifier_system = Column(String, nullable=True)
    reference_identifier_value = Column(String, nullable=True)
    reference_identifier_period_start = Column(
        DateTime(timezone=True), nullable=True
    )
    reference_identifier_period_end = Column(
        DateTime(timezone=True), nullable=True
    )

    communication_request = relationship(
        "CommunicationRequestModel", back_populates="reason_references"
    )
