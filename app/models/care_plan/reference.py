from sqlalchemy import BigInteger, Column, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base

# Which search parameter a CarePlanReference row feeds, the CarePlan element it is read from, and
# the resource types that element can point at (R4: basedOn / replaces / partOf -> CarePlan;
# careTeam -> CareTeam; addresses -> Condition; goal -> Goal; instantiatesCanonical -> canonical
# URLs of PlanDefinition | Questionnaire | Measure | ActivityDefinition | OperationDefinition).
REFERENCE_PARAMS = {
    "based-on": "basedOn",
    "replaces": "replaces",
    "part-of": "partOf",
    "care-team": "careTeam",
    "condition": "addresses",
    "goal": "goal",
    "instantiates-canonical": "instantiatesCanonical",
}
REFERENCE_TYPES = {
    "based-on": ("CarePlan",),
    "replaces": ("CarePlan",),
    "part-of": ("CarePlan",),
    "care-team": ("CareTeam",),
    "condition": ("Condition",),
    "goal": ("Goal",),
    "instantiates-canonical": (
        "PlanDefinition",
        "Questionnaire",
        "Measure",
        "ActivityDefinition",
        "OperationDefinition",
    ),
}


class CarePlanReference(Base):
    """Search index for the seven 0..* reference parameters `based-on`, `replaces`, `part-of`,
    `care-team`, `condition`, `goal` and `instantiates-canonical`: one row per Reference (or
    canonical URL) that has a value (one with only `display` cannot be matched by a reference
    search). `param` says which search parameter the row belongs to (see REFERENCE_PARAMS).
    Derived from CarePlanModel.content - never read to build a response.

    `reference_type` records which resource type a relative `Type/<id>` names - a plain string,
    not a Postgres enum. Every parameter except `instantiates-canonical` has one target, so a bare
    id works for it; `instantiates-canonical` holds canonical URLs, so its rows are usually just
    the raw string (a versioned `url|1.0` is matched by the unversioned `url` too).

      <param>             -> reference_type/reference_id (a relative Type/<id>) or
                             reference_reference (the raw string, for an absolute URL / canonical)
      <param>:identifier  -> reference_identifier_system/_value

    No ForeignKey on `reference_id` (the public id of another resource) and no UniqueConstraint: R4
    does not forbid listing the same reference twice."""

    __tablename__ = "care_plan_reference"
    __table_args__ = (
        Index(
            "ix_care_plan_reference_param_type_id",
            "param",
            "reference_type",
            "reference_id",
        ),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    care_plan_pk = Column(
        BigInteger, ForeignKey("care_plan.id"), nullable=False, index=True
    )
    param = Column(String, nullable=False)
    reference_reference = Column(String, nullable=True)
    reference_type = Column(String, nullable=True)
    reference_id = Column(BigInteger, nullable=True)
    reference_identifier_system = Column(String, nullable=True)
    reference_identifier_value = Column(String, nullable=True)

    care_plan = relationship("CarePlanModel", back_populates="references")
