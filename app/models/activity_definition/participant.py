from sqlalchemy import BigInteger, Column, Enum, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.activity_definition.enums import ActivityDefinitionParticipantType
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class ActivityDefinitionParticipant(TenantAuditMixin, Base):
    """ActivityDefinition.participant (0..*) child table."""

    __tablename__ = "activity_definition_participant"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    activity_definition_pk = Column(
        BigInteger, ForeignKey("activity_definition.id", ondelete="CASCADE"), nullable=False, index=True
    )

    type = Column(
        Enum(
            ActivityDefinitionParticipantType,
            name="activity_definition_participant_type",
        ),
        nullable=False,
    )
    role_text = Column(String, nullable=True)

    activity_definition = relationship("ActivityDefinitionModel", back_populates="participants")
    role_codings = relationship(
        "ActivityDefinitionParticipantRoleCoding",
        back_populates="participant",
        cascade="all, delete-orphan",
    )


class ActivityDefinitionParticipantRoleCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """ActivityDefinition.participant.role.coding (0..*) grandchild table."""

    __tablename__ = "activity_definition_participant_role_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    activity_definition_participant_id = Column(
        BigInteger,
        ForeignKey("activity_definition_participant.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    participant = relationship("ActivityDefinitionParticipant", back_populates="role_codings")
