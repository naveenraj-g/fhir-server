from sqlalchemy import BigInteger, Column, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.schemas.enums import AddressUse


class PatientAddress(Base):
    """Search index for `address`, `address-city`, `address-country`,
    `address-postalcode`, `address-state` and `address-use` (0..*): one row
    per Patient.address, holding only the Address parts those
    parameters match on. Derived from PatientModel.content — never read
    to build a response. Same shape as OrganizationAddress (see its
    docstring for the `*_norm` and `line` reasoning)."""

    __tablename__ = "patient_address"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    patient_pk = Column(
        BigInteger, ForeignKey("patient.id"), nullable=False, index=True
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

    patient = relationship("PatientModel", back_populates="addresses")
