from sqlalchemy import BigInteger, Column, Enum, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.plan_definition.enums import PlanDefinitionContactRole
from app.models.shared import FhirContactPointMixin, TenantAuditMixin


class PlanDefinitionContact(TenantAuditMixin, Base):
    """PlanDefinition contact details (contact, author, editor, reviewer, endorser)."""

    __tablename__ = "plan_definition_contact"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    plan_definition_pk = Column(
        BigInteger, ForeignKey("plan_definition.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role = Column(
        Enum(PlanDefinitionContactRole, name="plan_definition_contact_role"),
        nullable=False,
        index=True,
    )
    name = Column(String, nullable=True)

    plan_definition = relationship("PlanDefinitionModel", back_populates="contacts")
    telecoms = relationship(
        "PlanDefinitionContactTelecom",
        back_populates="contact",
        cascade="all, delete-orphan",
    )


class PlanDefinitionContactTelecom(FhirContactPointMixin, TenantAuditMixin, Base):
    """One entry of ContactDetail.telecom (0..*)."""

    __tablename__ = "plan_definition_contact_telecom"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    plan_definition_contact_id = Column(
        BigInteger,
        ForeignKey("plan_definition_contact.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    contact = relationship("PlanDefinitionContact", back_populates="telecoms")
