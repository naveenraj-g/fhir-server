from sqlalchemy import BigInteger, Column, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared.resource_types import ANY_RESOURCE_TYPES

# The reference parameters held in ClinicalImpressionReference, and the element each reads.
REFERENCE_PARAMS = {
    "problem": "problem",
    "investigation": "investigation.item",
    "finding-ref": "finding.itemReference",
    "supporting-info": "supportingInfo",
}
# R4 targets of each parameter.
PROBLEM_TYPES = ("Condition", "AllergyIntolerance")
INVESTIGATION_TYPES = (
    "RiskAssessment",
    "FamilyMemberHistory",
    "Observation",
    "Media",
    "DiagnosticReport",
    "ImagingStudy",
    "QuestionnaireResponse",
)
FINDING_TYPES = ("Condition", "Observation", "Media")
# `supportingInfo` is Reference(Any): R4 allows every resource type, so the whole R4 list is the target
# list (a plain reference search accepts any valid type; chaining and `_include` follow the
# types that are rebuilt on this server - see app/repository/_search_targets.py).
INFORMATION_TYPES = ANY_RESOURCE_TYPES
REFERENCE_TYPES = {
    "problem": PROBLEM_TYPES,
    "investigation": INVESTIGATION_TYPES,
    "finding-ref": FINDING_TYPES,
    "supporting-info": INFORMATION_TYPES,
}


class ClinicalImpressionReference(Base):
    """Search index for the four repeating reference parameters `problem`, `investigation`
    (investigation.item), `finding-ref` (finding.itemReference) and `supporting-info`
    (supportingInfo): one row per Reference that has a `reference` or an `identifier` (one with
    only `display` cannot be matched by a reference search). `param` says which parameter the
    row belongs to (see REFERENCE_PARAMS). Derived from ClinicalImpressionModel.content — never
    read to build a response.

    `reference_type` records which type a relative `Type/<id>` names — a plain string, not a
    Postgres enum (every one of these can point at several types, and `supporting-info` at any
    type; a search by bare id is ambiguous).

      <param>             -> reference_type/reference_id or reference_reference
      <param>:identifier  -> reference_identifier_system/_value

    No ForeignKey on `reference_id` and no UniqueConstraint: R4 does not forbid listing the
    same reference twice."""

    __tablename__ = "clinical_impression_reference"
    __table_args__ = (
        Index(
            "ix_clinical_impression_reference_param_type_id",
            "param",
            "reference_type",
            "reference_id",
        ),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    clinical_impression_pk = Column(
        BigInteger, ForeignKey("clinical_impression.id"), nullable=False, index=True
    )
    param = Column(String, nullable=False)
    reference_reference = Column(String, nullable=True)
    reference_type = Column(String, nullable=True)
    reference_id = Column(BigInteger, nullable=True)
    reference_identifier_system = Column(String, nullable=True)
    reference_identifier_value = Column(String, nullable=True)

    clinical_impression = relationship(
        "ClinicalImpressionModel", back_populates="references"
    )
