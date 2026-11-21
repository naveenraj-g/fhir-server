from sqlalchemy import BigInteger, Column, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base

# Which search parameter a ProcedureReference row feeds, the Procedure element it
# is read from, and the resource types that element can point at (R4: basedOn ->
# CarePlan | ServiceRequest; instantiatesCanonical -> canonical URLs of
# ActivityDefinition | Measure | OperationDefinition | PlanDefinition |
# Questionnaire; partOf -> MedicationAdministration | Observation | Procedure;
# reasonReference -> Condition | DiagnosticReport | DocumentReference |
# Observation | Procedure).
REFERENCE_PARAMS = {
    "based-on": "basedOn",
    "instantiates-canonical": "instantiatesCanonical",
    "part-of": "partOf",
    "reason-reference": "reasonReference",
}
REFERENCE_TYPES = {
    "based-on": ("CarePlan", "ServiceRequest"),
    "instantiates-canonical": (
        "ActivityDefinition",
        "Measure",
        "OperationDefinition",
        "PlanDefinition",
        "Questionnaire",
    ),
    "part-of": ("MedicationAdministration", "Observation", "Procedure"),
    "reason-reference": (
        "Condition",
        "DiagnosticReport",
        "DocumentReference",
        "Observation",
        "Procedure",
    ),
}


class ProcedureReference(Base):
    """Search index for the four 0..* reference parameters `based-on`,
    `instantiates-canonical`, `part-of` and `reason-reference`: one row per
    Reference (or canonical URL) that has a value (one with only `display` cannot
    be matched by a reference search). `param` says which search parameter the
    row belongs to (see REFERENCE_PARAMS). Derived from ProcedureModel.content —
    never read to build a response.

    `reference_type` records which resource type a relative `Type/<id>` names — a
    plain string, not a Postgres enum, because every one of these has several
    targets (a search by bare id is then ambiguous: `reason-reference=Type/id` or
    `:Type=id`). `instantiates-canonical` holds canonical URLs, so its rows are
    usually just the raw string (a versioned `url|1.0` is matched by the
    unversioned `url` too).

      <param>             -> reference_type/reference_id (a relative
                             Type/<id>) or reference_reference (the raw
                             string, for an absolute URL / canonical)
      <param>:identifier  -> reference_identifier_system/_value

    No ForeignKey on `reference_id` (the public id of another resource) and no
    UniqueConstraint: R4 does not forbid listing the same reference twice."""

    __tablename__ = "procedure_reference"
    __table_args__ = (
        Index(
            "ix_procedure_reference_param_type_id",
            "param",
            "reference_type",
            "reference_id",
        ),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    procedure_pk = Column(
        BigInteger, ForeignKey("procedure.id"), nullable=False, index=True
    )
    param = Column(String, nullable=False)
    reference_reference = Column(String, nullable=True)
    reference_type = Column(String, nullable=True)
    reference_id = Column(BigInteger, nullable=True)
    reference_identifier_system = Column(String, nullable=True)
    reference_identifier_value = Column(String, nullable=True)

    procedure = relationship("ProcedureModel", back_populates="references")
