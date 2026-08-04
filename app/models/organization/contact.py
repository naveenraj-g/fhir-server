from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import FHIRBase as Base
from app.schemas.enums import (
    AddressType,
    AddressUse,
    ContactPointSystem,
    ContactPointUse,
    HumanNameUse,
)

# ---------------------------------------------------------------------------
# contact (0..*) BackboneElement child table
# ---------------------------------------------------------------------------


class OrganizationContact(Base):
    __tablename__ = "organization_contact"

    id = Column(Integer, primary_key=True, autoincrement=True)
    organization_id = Column(
        Integer, ForeignKey("organization.id"), nullable=False, index=True
    )
    org_id = Column(String, nullable=False)

    # purpose (0..1) CodeableConcept
    purpose_system = Column(String, nullable=True)
    purpose_version = Column(String, nullable=True)
    purpose_code = Column(String, nullable=True)
    purpose_display = Column(String, nullable=True)
    purpose_text = Column(String, nullable=True)
    purpose_user_selected = Column(Boolean, nullable=True)

    # name (0..1) HumanName — flattened; given/prefix/suffix stored comma-separated
    name_use = Column(Enum(HumanNameUse, name="human_name_use"), nullable=True)
    name_text = Column(String, nullable=True)
    name_family = Column(String, nullable=True)
    name_given = Column(Text, nullable=True)  # comma-separated
    name_prefix = Column(Text, nullable=True)  # comma-separated
    name_suffix = Column(Text, nullable=True)  # comma-separated
    name_period_start = Column(DateTime(timezone=True), nullable=True)
    name_period_end = Column(DateTime(timezone=True), nullable=True)

    # address (0..1) Address — flattened
    address_use = Column(Enum(AddressUse, name="address_use"), nullable=True)
    address_type = Column(Enum(AddressType, name="address_type"), nullable=False)
    address_text = Column(String, nullable=True)
    address_line = Column(Text, nullable=True)  # comma-separated
    address_city = Column(String, nullable=False)
    address_district = Column(String, nullable=True)
    address_state = Column(String, nullable=False)
    address_postal_code = Column(String, nullable=False)
    address_country = Column(String, nullable=False)
    address_period_start = Column(DateTime(timezone=True), nullable=True)
    address_period_end = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, nullable=False)
    updated_by = Column(String, nullable=True)

    organization = relationship("OrganizationModel", back_populates="contacts")
    telecoms = relationship(
        "OrganizationContactTelecom",
        back_populates="contact",
        cascade="all, delete-orphan",
    )


# ---------------------------------------------------------------------------
# contact.telecom (0..*) ContactPoint grandchild table
# ---------------------------------------------------------------------------


class OrganizationContactTelecom(Base):
    __tablename__ = "organization_contact_telecom"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contact_id = Column(
        Integer, ForeignKey("organization_contact.id"), nullable=False, index=True
    )
    org_id = Column(String, nullable=False)
    system = Column(
        Enum(ContactPointSystem, name="contact_point_system"), nullable=False
    )
    value = Column(String, nullable=False)
    use = Column(Enum(ContactPointUse, name="contact_point_use"), nullable=True)
    rank = Column(Integer, nullable=True)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, nullable=False)
    updated_by = Column(String, nullable=True)

    contact = relationship("OrganizationContact", back_populates="telecoms")
