from sqlalchemy import BigInteger, Column, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base

# Which search parameter an AppointmentReference row feeds, the Appointment
# element it is read from, and the resource types that element can point at
# (R4: basedOn -> ServiceRequest, reasonReference -> Condition | Procedure |
# Observation | ImmunizationRecommendation, slot -> Slot,
# supportingInformation -> Any).
REFERENCE_PARAMS = {
    "based-on": "basedOn",
    "reason-reference": "reasonReference",
    "slot": "slot",
    "supporting-info": "supportingInformation",
}
REFERENCE_TYPES = {
    "based-on": ("ServiceRequest",),
    "reason-reference": (
        "Condition",
        "Procedure",
        "Observation",
        "ImmunizationRecommendation",
    ),
    "slot": ("Slot",),
    # Reference(Any): no finite list, so any `Type/<id>` is indexed (None).
    "supporting-info": None,
}


class AppointmentReference(Base):
    """Search index for the four 0..* reference parameters `based-on`,
    `reason-reference`, `slot` and `supporting-info`: one row per Reference
    that has a `reference` or an `identifier` (one with only `display` can't
    be matched by a reference search). `param` says which search parameter
    the row belongs to (see REFERENCE_PARAMS). Derived from
    AppointmentModel.content — never read to build a response.

    `reference_type` records which resource type a relative `Type/<id>`
    names — a plain string, not a Postgres enum, because `supporting-info` is
    Reference(Any) and `reason-reference` has several targets (a search by
    bare id is then ambiguous: `reason-reference=Type/id` or `:Type=id`).

      <param>             -> reference_type/reference_id (a relative
                             Type/<id>) or reference_reference (the raw
                             string, for an absolute URL)
      <param>:identifier  -> reference_identifier_system/_value

    No ForeignKey on `reference_id` (the public id of another resource) and no
    UniqueConstraint: R4 doesn't forbid listing the same reference twice."""

    __tablename__ = "appointment_reference"
    __table_args__ = (
        Index(
            "ix_appointment_reference_param_type_id",
            "param",
            "reference_type",
            "reference_id",
        ),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    appointment_pk = Column(
        BigInteger, ForeignKey("appointment.id"), nullable=False, index=True
    )
    param = Column(String, nullable=False)
    reference_reference = Column(String, nullable=True)
    reference_type = Column(String, nullable=True)
    reference_id = Column(BigInteger, nullable=True)
    reference_identifier_system = Column(String, nullable=True)
    reference_identifier_value = Column(String, nullable=True)

    appointment = relationship("AppointmentModel", back_populates="references")
