from sqlalchemy import BigInteger, Column, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared.resource_types import ANY_RESOURCE_TYPES

# Which search parameter a MeasureReportReference row feeds, the MeasureReport element it is read
# from, and the resource types that element points at (R4: `measure` is the canonical URL of a
# Measure, 1..1; `evaluatedResource` is a list of Reference(Any)).
REFERENCE_PARAMS = {
    "measure": "measure",
    "evaluated-resource": "evaluatedResource",
}
REFERENCE_TYPES = {
    "measure": ("Measure",),
    "evaluated-resource": ANY_RESOURCE_TYPES,
}

# The R4 targets of the 0..1 references held as columns on the row.
SUBJECT_TYPES = (
    "Practitioner",
    "Group",
    "Device",
    "Patient",
    "PractitionerRole",
    "RelatedPerson",
    "Location",
)
REPORTER_TYPES = ("Practitioner", "PractitionerRole", "Location", "Organization")


class MeasureReportReference(Base):
    """Search index for the `measure` and `evaluated-resource` reference parameters: one row per
    canonical URL / Reference that has a value (one with only `display` cannot be matched by a
    reference search). `param` says which search parameter the row belongs to (see
    REFERENCE_PARAMS). Derived from MeasureReportModel.content - never read to build a response.

    `reference_type` records which resource type a relative `Type/<id>` names - a plain string,
    not a Postgres enum. `measure` holds a canonical URL (a string, not a Reference object), so
    its row is usually just the raw string (a versioned `url|1.0` is matched by the unversioned
    `url` too, and resolved against a stored Measure's own `url`); `evaluated-resource` is
    Reference(Any), so a search by bare id is ambiguous (`evaluated-resource=Type/id` or
    `:Type=id`).

      <param>             -> reference_type/reference_id (a relative Type/<id>) or
                             reference_reference (the raw string, for an absolute URL / canonical)
      <param>:identifier  -> reference_identifier_system/_value

    No ForeignKey on `reference_id` (the public id of another resource) and no UniqueConstraint:
    R4 does not forbid listing the same reference twice."""

    __tablename__ = "measure_report_reference"
    __table_args__ = (
        Index(
            "ix_measure_report_reference_param_type_id",
            "param",
            "reference_type",
            "reference_id",
        ),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    measure_report_pk = Column(
        BigInteger, ForeignKey("measure_report.id"), nullable=False, index=True
    )
    param = Column(String, nullable=False)
    reference_reference = Column(String, nullable=True)
    reference_type = Column(String, nullable=True)
    reference_id = Column(BigInteger, nullable=True)
    reference_identifier_system = Column(String, nullable=True)
    reference_identifier_value = Column(String, nullable=True)

    measure_report = relationship("MeasureReportModel", back_populates="references")
