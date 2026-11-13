from sqlalchemy import BigInteger, Column, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.schemas.enums import AddressUse


class OrganizationAddress(Base):
    """Search index for `address`, `address-city`, `address-country`,
    `address-postalcode`, `address-state` and `address-use` (0..*): one row
    per Organization.address, holding only the Address parts those
    parameters match on. Derived from OrganizationModel.content — never read
    to build a response.

    Every string part is stored as written (for `:exact`) and normalized
    (`*_norm`: accents stripped, case-folded — for the default starts-with
    and `:contains`). `line` stays an array so each line is matched on its
    own, as R4's starts-with requires.

    Deliberately not FhirAddressMixin: that mixin models a full Address
    *embed* (type, period, ...); this is an index, so it carries only the
    searched parts."""

    __tablename__ = "organization_address"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    organization_pk = Column(
        BigInteger, ForeignKey("organization.id"), nullable=False, index=True
    )
    use = Column(Enum(AddressUse, name="address_use"), nullable=True)
    text = Column(String, nullable=True)
    text_norm = Column(String, nullable=True)
    line = Column(ARRAY(String), nullable=True)
    line_norm = Column(ARRAY(String), nullable=True)
    city = Column(String, nullable=True)
    city_norm = Column(String, nullable=True)
    district = Column(String, nullable=True)
    district_norm = Column(String, nullable=True)
    state = Column(String, nullable=True)
    state_norm = Column(String, nullable=True)
    postal_code = Column(String, nullable=True)
    postal_code_norm = Column(String, nullable=True)
    country = Column(String, nullable=True)
    country_norm = Column(String, nullable=True)

    organization = relationship("OrganizationModel", back_populates="addresses")
