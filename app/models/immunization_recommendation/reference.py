from sqlalchemy import BigInteger, Column, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.models.shared.resource_types import ANY_RESOURCE_TYPES
from app.core.database import FHIRBase as Base

# The two reference parameters held in ImmunizationRecommendationReference, and the
# element each reads.
REFERENCE_PARAMS = {
    "support": "recommendation.supportingImmunization",
    "information": "recommendation.supportingPatientInformation",
}
# R4 targets of `support`.
SUPPORT_TYPES = ("Immunization", "ImmunizationEvaluation")
# `supportingPatientInformation` is Reference(Any): R4 allows every resource type, so the whole R4 list is the target
# list (a plain reference search accepts any valid type; chaining and `_include` follow the
# types that are rebuilt on this server - see app/repository/_search_targets.py).
INFORMATION_TYPES = ANY_RESOURCE_TYPES
REFERENCE_TYPES = {"support": SUPPORT_TYPES, "information": INFORMATION_TYPES}


class ImmunizationRecommendationReference(Base):
    """Search index for the two repeating reference parameters `support`
    (recommendation.supportingImmunization) and `information`
    (recommendation.supportingPatientInformation): one row per Reference that has a
    `reference` or an `identifier` (one with only `display` cannot be matched by a
    reference search). `param` says which parameter the row belongs to. Derived from
    ImmunizationRecommendationModel.content — never read to build a response.

    `reference_type` records which type a relative `Type/<id>` names — a plain
    string, not a Postgres enum (both elements can point at several types, and
    `information` at any type; a search by bare id is ambiguous).

      <param>             -> reference_type/reference_id or reference_reference
      <param>:identifier  -> reference_identifier_system/_value

    No ForeignKey on `reference_id` and no UniqueConstraint: R4 does not forbid
    listing the same reference twice."""

    __tablename__ = "immunization_recommendation_reference"
    __table_args__ = (
        Index(
            "ix_immunization_recommendation_reference_param_type_id",
            "param",
            "reference_type",
            "reference_id",
        ),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    immunization_recommendation_pk = Column(
        BigInteger,
        ForeignKey("immunization_recommendation.id"),
        nullable=False,
        index=True,
    )
    param = Column(String, nullable=False)
    reference_reference = Column(String, nullable=True)
    reference_type = Column(String, nullable=True)
    reference_id = Column(BigInteger, nullable=True)
    reference_identifier_system = Column(String, nullable=True)
    reference_identifier_value = Column(String, nullable=True)

    immunization_recommendation = relationship(
        "ImmunizationRecommendationModel", back_populates="references"
    )
