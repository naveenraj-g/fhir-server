from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base

# Search parameters held in ObservationValue, and the element each reads. `slot` 0 is the
# Observation itself; slot n >= 1 is its n-th component.
VALUE_PARAMS = {
    "value-quantity": "value[x] as Quantity",
    "component-value-quantity": "component.value[x] as Quantity",
    "value-string": "value[x] as string | value[x] as CodeableConcept .text",
    "value-date": "value[x] as dateTime | Period",
}


class ObservationValue(Base):
    """Search index for the value[x] search parameters that are not CodeableConcept tokens: one
    row per value occurrence, told apart by `param` (see VALUE_PARAMS) and tied to the element it
    came from by `slot` (0 = the Observation, n = its n-th component), so a composite search can
    pair a code with a value of the same element. Derived from ObservationModel.content — never
    read to build a response.

      value-quantity, component-value-quantity -> quantity_value/_system/_code/_unit (a Quantity;
                                                  SampledData is not indexed)
      value-string                             -> string_norm (valueString, and the `text` of a
                                                  valueCodeableConcept)
      value-date                               -> date_start/_end (the half-open range a
                                                  valueDateTime or valuePeriod covers)

    Only the columns that apply to a row's `param` are set."""

    __tablename__ = "observation_value"
    __table_args__ = (Index("ix_observation_value_param_slot", "param", "slot"),)

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    observation_pk = Column(
        BigInteger, ForeignKey("observation.id"), nullable=False, index=True
    )
    param = Column(String, nullable=False)
    slot = Column(Integer, nullable=False, default=0)
    quantity_value = Column(Numeric, nullable=True)
    quantity_system = Column(String, nullable=True)
    quantity_code = Column(String, nullable=True)
    quantity_unit = Column(String, nullable=True)
    string_norm = Column(String, nullable=True)
    date_start = Column(DateTime(timezone=True), nullable=True)
    date_end = Column(DateTime(timezone=True), nullable=True)

    observation = relationship("ObservationModel", back_populates="values")
