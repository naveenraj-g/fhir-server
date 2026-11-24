from sqlalchemy import BigInteger, Column, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base

# Search parameters held in PlanDefinitionReference, and the PlanDefinition element each
# reads: the five relatedArtifact types (`resource`, a canonical URL), for `depends-on` also
# `library` (a canonical(Library)), and `definition` (`action.definitionCanonical`).
# R4's targets of `definition`: the canonical of an activity or plan the action performs.
DEFINITION_TYPES = ("Questionnaire", "PlanDefinition", "ActivityDefinition")
REFERENCE_PARAMS = {
    "composed-of": "relatedArtifact.where(type='composed-of').resource",
    "depends-on": "relatedArtifact.where(type='depends-on').resource | library",
    "derived-from": "relatedArtifact.where(type='derived-from').resource",
    "predecessor": "relatedArtifact.where(type='predecessor').resource",
    "successor": "relatedArtifact.where(type='successor').resource",
    "definition": "action.definition (definitionCanonical, at every depth)",
}


class PlanDefinitionReference(Base):
    """Search index for the five `relatedArtifact` reference parameters (`composed-of`,
    `depends-on`, `derived-from`, `predecessor`, `successor`) and `definition` (every action's
    `definitionCanonical`): one row per canonical URL. `param`
    says which search parameter the row belongs to (see REFERENCE_PARAMS). Derived from
    PlanDefinitionModel.content - never read to build a response.

    R4's `RelatedArtifact.resource` is a canonical URL (a string, not a Reference object): the
    row keeps the raw string in `reference_reference` (a versioned `url|1.0` is also found by the
    unversioned `url`), and a relative `Type/<id>` is additionally resolved into
    `reference_type` / `reference_id` (a plain string, not a Postgres enum) so a search by
    `Type/<id>`, chaining and `_include` work for it.

    No ForeignKey on `reference_id` (the public id of another resource) and no UniqueConstraint:
    R4 does not forbid listing the same artifact twice."""

    __tablename__ = "plan_definition_reference"
    __table_args__ = (
        Index(
            "ix_plan_definition_reference_param_type_id",
            "param",
            "reference_type",
            "reference_id",
        ),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    plan_definition_pk = Column(
        BigInteger, ForeignKey("plan_definition.id"), nullable=False, index=True
    )
    param = Column(String, nullable=False)
    reference_reference = Column(String, nullable=True)
    reference_type = Column(String, nullable=True)
    reference_id = Column(BigInteger, nullable=True)

    plan_definition = relationship("PlanDefinitionModel", back_populates="references")
