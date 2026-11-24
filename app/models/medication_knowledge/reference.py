from sqlalchemy import BigInteger, Column, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base

# Which search parameter a MedicationKnowledgeReference row feeds, the element it is read from,
# and the resource types that element can point at (R4: ingredient.itemReference ->
# Substance; monograph.source -> DocumentReference | Media).
REFERENCE_PARAMS = {
    "ingredient": "ingredient.itemReference",
    "monograph": "monograph.source",
}
REFERENCE_TYPES = {
    "ingredient": ("Substance",),
    "monograph": ("DocumentReference", "Media"),
}


class MedicationKnowledgeReference(Base):
    """Search index for the `ingredient` and `monograph` reference parameters: one row per
    Reference that has a value (one with only `display` cannot be matched by a reference
    search). `param` says which search parameter the row belongs to (see REFERENCE_PARAMS).
    Derived from MedicationKnowledgeModel.content - never read to build a response.

    `reference_type` records which resource type a relative `Type/<id>` names - a plain
    string, not a Postgres enum.

      <param>             -> reference_type/reference_id (a relative Type/<id>) or
                             reference_reference (the raw string, for an absolute URL)
      <param>:identifier  -> reference_identifier_system/_value

    No ForeignKey on `reference_id` (the public id of another resource) and no
    UniqueConstraint: R4 does not forbid listing the same reference twice."""

    __tablename__ = "medication_knowledge_reference"
    __table_args__ = (
        Index(
            "ix_medication_knowledge_reference_param_type_id",
            "param",
            "reference_type",
            "reference_id",
        ),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_knowledge_pk = Column(
        BigInteger, ForeignKey("medication_knowledge.id"), nullable=False, index=True
    )
    param = Column(String, nullable=False)
    reference_reference = Column(String, nullable=True)
    reference_type = Column(String, nullable=True)
    reference_id = Column(BigInteger, nullable=True)
    reference_identifier_system = Column(String, nullable=True)
    reference_identifier_value = Column(String, nullable=True)

    medication_knowledge = relationship(
        "MedicationKnowledgeModel", back_populates="references"
    )
