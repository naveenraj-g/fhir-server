from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    String,
)
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.enums import IdentifierUse
from app.models.immunization.enums import ImmunizationPerformerActorReferenceType
from app.models.shared import TenantAuditMixin
from app.models.shared.datatypes import FhirCodingMixin


class ImmunizationPerformerModel(TenantAuditMixin, Base):
    """Immunization.performer (0..* BackboneElement) child table."""

    __tablename__ = "immunization_performer"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    immunization_pk = Column(
        BigInteger, ForeignKey("immunization.id"), nullable=False, index=True
    )

    function_text = Column(String, nullable=True)

    # actor (1..1 Reference(Practitioner | PractitionerRole | Organization))
    actor_reference = Column(String, nullable=False)
    actor_type = Column(
        Enum(
            ImmunizationPerformerActorReferenceType,
            name="immunization_performer_actor_reference_type",
        ),
        nullable=False,
    )
    actor_id = Column(BigInteger, nullable=True, index=True)
    actor_display = Column(String, nullable=True)

    # actor.identifier fallback (11 columns)
    actor_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    actor_identifier_type_system = Column(String, nullable=True)
    actor_identifier_type_version = Column(String, nullable=True)
    actor_identifier_type_code = Column(String, nullable=True)
    actor_identifier_type_display = Column(String, nullable=True)
    actor_identifier_type_user_selected = Column(Boolean, nullable=True)
    actor_identifier_type_text = Column(String, nullable=True)
    actor_identifier_system = Column(String, nullable=True)
    actor_identifier_value = Column(String, nullable=True)
    actor_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    actor_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    immunization = relationship("ImmunizationModel", back_populates="performers")
    function_codings = relationship(
        "ImmunizationPerformerFunctionCodingModel",
        back_populates="performer",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class ImmunizationPerformerFunctionCodingModel(FhirCodingMixin, TenantAuditMixin, Base):
    """Immunization.performer.function.coding (0..* Coding) grandchild table."""

    __tablename__ = "immunization_performer_function_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    performer_id = Column(
        BigInteger, ForeignKey("immunization_performer.id"), nullable=False, index=True
    )

    performer = relationship("ImmunizationPerformerModel", back_populates="function_codings")
