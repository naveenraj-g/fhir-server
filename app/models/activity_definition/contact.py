from sqlalchemy import BigInteger, Column, Enum, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.activity_definition.enums import ActivityDefinitionContactRole
from app.models.shared import FhirContactPointMixin, TenantAuditMixin


class ActivityDefinitionContact(TenantAuditMixin, Base):
    """ActivityDefinition contact details (contact, author, editor, reviewer, endorser)."""

    __tablename__ = "activity_definition_contact"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    activity_definition_pk = Column(
        BigInteger, ForeignKey("activity_definition.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role = Column(
        Enum(ActivityDefinitionContactRole, name="activity_definition_contact_role"),
        nullable=False,
        index=True,
    )
    name = Column(String, nullable=True)

    activity_definition = relationship("ActivityDefinitionModel", back_populates="contacts")
    telecoms = relationship(
        "ActivityDefinitionContactTelecom",
        back_populates="contact",
        cascade="all, delete-orphan",
    )


class ActivityDefinitionContactTelecom(FhirContactPointMixin, TenantAuditMixin, Base):
    """One entry of ContactDetail.telecom (0..*)."""

    __tablename__ = "activity_definition_contact_telecom"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    activity_definition_contact_id = Column(
        BigInteger,
        ForeignKey("activity_definition_contact.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    contact = relationship("ActivityDefinitionContact", back_populates="telecoms")
