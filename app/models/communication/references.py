from sqlalchemy import BigInteger, Boolean, Column, DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.communication.enums import (
    CommunicationInResponseToReferenceType,
    CommunicationReasonReferenceType,
    CommunicationRecipientReferenceType,
)
from app.models.enums import IdentifierUse
from app.models.shared import TenantAuditMixin


class CommunicationBasedOn(TenantAuditMixin, Base):
    """Communication.basedOn (0..*) child table. Reference(Resource)."""

    __tablename__ = "communication_based_on"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    communication_pk = Column(
        BigInteger,
        ForeignKey("communication.id"),
        nullable=False,
        index=True,
    )

    reference_reference = Column(String, nullable=True)
    reference_type = Column(String, nullable=True)
    reference_id = Column(BigInteger, nullable=True, index=True)
    reference_display = Column(String, nullable=True)

    reference_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    reference_identifier_type_system = Column(String, nullable=True)
    reference_identifier_type_version = Column(String, nullable=True)
    reference_identifier_type_code = Column(String, nullable=True)
    reference_identifier_type_display = Column(String, nullable=True)
    reference_identifier_type_text = Column(String, nullable=True)
    reference_identifier_type_user_selected = Column(Boolean, nullable=True)
    reference_identifier_system = Column(String, nullable=True)
    reference_identifier_value = Column(String, nullable=True)
    reference_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    reference_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    communication = relationship(
        "CommunicationModel", back_populates="based_on_list"
    )


class CommunicationPartOf(TenantAuditMixin, Base):
    """Communication.partOf (0..*) child table. Reference(Resource)."""

    __tablename__ = "communication_part_of"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    communication_pk = Column(
        BigInteger,
        ForeignKey("communication.id"),
        nullable=False,
        index=True,
    )

    reference_reference = Column(String, nullable=True)
    reference_type = Column(String, nullable=True)
    reference_id = Column(BigInteger, nullable=True, index=True)
    reference_display = Column(String, nullable=True)

    reference_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    reference_identifier_type_system = Column(String, nullable=True)
    reference_identifier_type_version = Column(String, nullable=True)
    reference_identifier_type_code = Column(String, nullable=True)
    reference_identifier_type_display = Column(String, nullable=True)
    reference_identifier_type_text = Column(String, nullable=True)
    reference_identifier_type_user_selected = Column(Boolean, nullable=True)
    reference_identifier_system = Column(String, nullable=True)
    reference_identifier_value = Column(String, nullable=True)
    reference_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    reference_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    communication = relationship(
        "CommunicationModel", back_populates="part_of_list"
    )


class CommunicationInResponseTo(TenantAuditMixin, Base):
    """Communication.inResponseTo (0..*) child table. Reference(Communication)."""

    __tablename__ = "communication_in_response_to"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    communication_pk = Column(
        BigInteger,
        ForeignKey("communication.id"),
        nullable=False,
        index=True,
    )

    reference_reference = Column(String, nullable=True)
    reference_type = Column(
        Enum(
            CommunicationInResponseToReferenceType,
            name="communication_in_response_to_reference_type",
        ),
        nullable=True,
    )
    reference_id = Column(BigInteger, nullable=True, index=True)
    reference_display = Column(String, nullable=True)

    reference_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    reference_identifier_type_system = Column(String, nullable=True)
    reference_identifier_type_version = Column(String, nullable=True)
    reference_identifier_type_code = Column(String, nullable=True)
    reference_identifier_type_display = Column(String, nullable=True)
    reference_identifier_type_text = Column(String, nullable=True)
    reference_identifier_type_user_selected = Column(Boolean, nullable=True)
    reference_identifier_system = Column(String, nullable=True)
    reference_identifier_value = Column(String, nullable=True)
    reference_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    reference_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    communication = relationship(
        "CommunicationModel", back_populates="in_response_to_list"
    )


class CommunicationAbout(TenantAuditMixin, Base):
    """Communication.about (0..*) child table. Reference(Resource)."""

    __tablename__ = "communication_about"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    communication_pk = Column(
        BigInteger,
        ForeignKey("communication.id"),
        nullable=False,
        index=True,
    )

    reference_reference = Column(String, nullable=True)
    reference_type = Column(String, nullable=True)
    reference_id = Column(BigInteger, nullable=True, index=True)
    reference_display = Column(String, nullable=True)

    reference_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    reference_identifier_type_system = Column(String, nullable=True)
    reference_identifier_type_version = Column(String, nullable=True)
    reference_identifier_type_code = Column(String, nullable=True)
    reference_identifier_type_display = Column(String, nullable=True)
    reference_identifier_type_text = Column(String, nullable=True)
    reference_identifier_type_user_selected = Column(Boolean, nullable=True)
    reference_identifier_system = Column(String, nullable=True)
    reference_identifier_value = Column(String, nullable=True)
    reference_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    reference_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    communication = relationship(
        "CommunicationModel", back_populates="about_list"
    )


class CommunicationRecipient(TenantAuditMixin, Base):
    """Communication.recipient (0..*) child table. Reference(Device|Organization|Patient|Practitioner|PractitionerRole|RelatedPerson|Group|CareTeam|HealthcareService)."""

    __tablename__ = "communication_recipient"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    communication_pk = Column(
        BigInteger,
        ForeignKey("communication.id"),
        nullable=False,
        index=True,
    )

    reference_reference = Column(String, nullable=True)
    reference_type = Column(
        Enum(
            CommunicationRecipientReferenceType,
            name="communication_recipient_reference_type",
        ),
        nullable=True,
    )
    reference_id = Column(BigInteger, nullable=True, index=True)
    reference_display = Column(String, nullable=True)

    reference_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    reference_identifier_type_system = Column(String, nullable=True)
    reference_identifier_type_version = Column(String, nullable=True)
    reference_identifier_type_code = Column(String, nullable=True)
    reference_identifier_type_display = Column(String, nullable=True)
    reference_identifier_type_text = Column(String, nullable=True)
    reference_identifier_type_user_selected = Column(Boolean, nullable=True)
    reference_identifier_system = Column(String, nullable=True)
    reference_identifier_value = Column(String, nullable=True)
    reference_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    reference_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    communication = relationship(
        "CommunicationModel", back_populates="recipients"
    )


class CommunicationReasonReference(TenantAuditMixin, Base):
    """Communication.reasonReference (0..*) child table. Reference(Condition|Observation|DiagnosticReport|DocumentReference)."""

    __tablename__ = "communication_reason_reference"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    communication_pk = Column(
        BigInteger,
        ForeignKey("communication.id"),
        nullable=False,
        index=True,
    )

    reference_reference = Column(String, nullable=True)
    reference_type = Column(
        Enum(
            CommunicationReasonReferenceType,
            name="communication_reason_reference_type",
        ),
        nullable=True,
    )
    reference_id = Column(BigInteger, nullable=True, index=True)
    reference_display = Column(String, nullable=True)

    reference_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    reference_identifier_type_system = Column(String, nullable=True)
    reference_identifier_type_version = Column(String, nullable=True)
    reference_identifier_type_code = Column(String, nullable=True)
    reference_identifier_type_display = Column(String, nullable=True)
    reference_identifier_type_text = Column(String, nullable=True)
    reference_identifier_type_user_selected = Column(Boolean, nullable=True)
    reference_identifier_system = Column(String, nullable=True)
    reference_identifier_value = Column(String, nullable=True)
    reference_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    reference_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    communication = relationship(
        "CommunicationModel", back_populates="reason_references"
    )
