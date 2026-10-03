from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    String,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import (
    FhirAddressMixin,
    FhirCodingMixin,
    FhirContactPointMixin,
    TenantAuditMixin,
)
from app.schemas.enums import HumanNameUse

# ---------------------------------------------------------------------------
# contact (0..*) BackboneElement child table
# ---------------------------------------------------------------------------


class OrganizationContact(FhirAddressMixin, TenantAuditMixin, Base):
    """contact.address uses FhirAddressMixin with `_address_prefix = "address_"`
    — same DB column names as before (address_city, address_use, etc.,
    keeping them visually grouped apart from this table's purpose_*/name_*
    columns), but accessed in Python as `self.city`/`self.use`/etc. rather
    than `self.address_city`/`self.address_use`. See FhirAddressMixin's
    docstring for why a prefix-parameterized mixin (not a plain one) is
    needed here."""

    __tablename__ = "organization_contact"
    _address_prefix = "address_"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    # Containment FK — see identifier.py's organization_pk for why this
    # isn't named organization_id.
    organization_pk = Column(
        BigInteger, ForeignKey("organization.id"), nullable=False, index=True
    )

    # purpose (0..1 CodeableConcept) — extensible binding. purpose_text
    # stays flattened (sibling of coding[], not part of it); purpose's
    # coding[] is a real 0..* child table (OrganizationContactPurposeCoding)
    # for the same org-custom-code + standard-terminology-crosswalk reason
    # as OrganizationType's coding — see type.py.
    purpose_text = Column(String, nullable=True)

    # name (0..1) HumanName — flattened; given/prefix/suffix are real
    # Postgres arrays, not comma-separated text.
    name_use = Column(Enum(HumanNameUse, name="human_name_use"), nullable=True)
    name_text = Column(String, nullable=True)
    name_family = Column(String, nullable=True)
    name_given = Column(ARRAY(String), nullable=True)
    name_prefix = Column(ARRAY(String), nullable=True)
    name_suffix = Column(ARRAY(String), nullable=True)
    name_period_start = Column(DateTime(timezone=True), nullable=True)
    name_period_end = Column(DateTime(timezone=True), nullable=True)

    # address (0..1 Address) — columns provided by FhirAddressMixin above
    # (self.use, self.type, self.city, etc. — DB columns stay
    # address_use/address_type/address_city/etc. via _address_prefix). No
    # org-2 CHECK/validator rule here: org-2 is scoped to
    # Organization.address specifically in the base spec text, not
    # Organization.contact.address — applying it here anyway would be a
    # stricter-than-spec invention.

    organization = relationship("OrganizationModel", back_populates="contacts")
    telecoms = relationship(
        "OrganizationContactTelecom",
        back_populates="contact",
        cascade="all, delete-orphan",
    )
    purpose_codings = relationship(
        "OrganizationContactPurposeCoding",
        back_populates="contact",
        cascade="all, delete-orphan",
    )


# ---------------------------------------------------------------------------
# contact.telecom (0..*) ContactPoint grandchild table
# ---------------------------------------------------------------------------


class OrganizationContactTelecom(FhirContactPointMixin, TenantAuditMixin, Base):
    """No DB-level CHECK constraint — the rank>0 (positiveInt) rule is
    enforced by the FHIR validator layer instead — see OrganizationModel's
    docstring (core.py) for why."""

    __tablename__ = "organization_contact_telecom"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    contact_id = Column(
        BigInteger, ForeignKey("organization_contact.id"), nullable=False, index=True
    )

    contact = relationship("OrganizationContact", back_populates="telecoms")


# ---------------------------------------------------------------------------
# contact.purpose.coding (0..*) grandchild table
# ---------------------------------------------------------------------------


class OrganizationContactPurposeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Organization.contact.purpose.coding (0..*)."""

    __tablename__ = "organization_contact_purpose_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    contact_id = Column(
        BigInteger, ForeignKey("organization_contact.id"), nullable=False, index=True
    )

    contact = relationship("OrganizationContact", back_populates="purpose_codings")
