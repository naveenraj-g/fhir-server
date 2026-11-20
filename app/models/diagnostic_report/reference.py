from sqlalchemy import BigInteger, Column, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base

# Which search parameter a DiagnosticReportReference row feeds, the DiagnosticReport
# element it is read from, and the resource types that element can point at (R4:
# basedOn -> CarePlan | ImmunizationRecommendation | MedicationRequest |
# NutritionOrder | ServiceRequest; media.link -> Media; result -> Observation;
# specimen -> Specimen).
REFERENCE_PARAMS = {
    "based-on": "basedOn",
    "media": "media.link",
    "result": "result",
    "specimen": "specimen",
}
REFERENCE_TYPES = {
    "based-on": ("CarePlan", "ImmunizationRecommendation", "MedicationRequest", "NutritionOrder", "ServiceRequest"),
    "media": ("Media",),
    "result": ("Observation",),
    "specimen": ("Specimen",),
}


class DiagnosticReportReference(Base):
    """Search index for the four 0..* reference parameters `based-on`, `media`,
    `result` and `specimen`: one row per Reference that has a `reference` or an
    `identifier` (one with only `display` cannot be matched by a reference
    search). `param` says which search parameter the row belongs to (see
    REFERENCE_PARAMS). Derived from DiagnosticReportModel.content — never read to
    build a response.

    `reference_type` records which resource type a relative `Type/<id>` names — a
    plain string, not a Postgres enum, because `based-on` has several targets (a
    search by bare id is then ambiguous: `based-on=Type/id` or `:Type=id`).

      <param>             -> reference_type/reference_id (a relative
                             Type/<id>) or reference_reference (the raw
                             string, for an absolute URL)
      <param>:identifier  -> reference_identifier_system/_value

    No ForeignKey on `reference_id` (the public id of another resource) and no
    UniqueConstraint: R4 does not forbid listing the same reference twice."""

    __tablename__ = "diagnostic_report_reference"
    __table_args__ = (Index("ix_diagnostic_report_reference_param_type_id", "param", "reference_type", "reference_id"),)

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    diagnostic_report_pk = Column(BigInteger, ForeignKey("diagnostic_report.id"), nullable=False, index=True)
    param = Column(String, nullable=False)
    reference_reference = Column(String, nullable=True)
    reference_type = Column(String, nullable=True)
    reference_id = Column(BigInteger, nullable=True)
    reference_identifier_system = Column(String, nullable=True)
    reference_identifier_value = Column(String, nullable=True)

    diagnostic_report = relationship("DiagnosticReportModel", back_populates="references")
