from sqlalchemy import BigInteger, Column, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base


class ConditionEvidenceDetail(Base):
    """Search index for `evidence-detail` (Condition.evidence.detail, 0..*
    Reference(Any)): one row per Reference that has a `reference` or an
    `identifier` (one with only `display` cannot be matched by a reference
    search). Derived from ConditionModel.content — never read to build a
    response.

    `reference_type` records which resource type a relative `Type/<id>` names —
    a plain string, not a Postgres enum, because the element is Reference(Any)
    (a search by bare id is therefore ambiguous: `evidence-detail=Type/id` or
    `:Type=id`).

      evidence-detail             -> reference_type/reference_id (a relative
                                     Type/<id>) or reference_reference (the raw
                                     string, for an absolute URL)
      evidence-detail:identifier  -> reference_identifier_system/_value

    No ForeignKey on `reference_id` (the public id of another resource) and no
    UniqueConstraint: R4 does not forbid listing the same reference twice."""

    __tablename__ = "condition_evidence_detail"
    __table_args__ = (
        Index("ix_condition_evidence_detail_type_id", "reference_type", "reference_id"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    condition_pk = Column(
        BigInteger, ForeignKey("condition.id"), nullable=False, index=True
    )
    reference_reference = Column(String, nullable=True)
    reference_type = Column(String, nullable=True)
    reference_id = Column(BigInteger, nullable=True)
    reference_identifier_system = Column(String, nullable=True)
    reference_identifier_value = Column(String, nullable=True)

    condition = relationship("ConditionModel", back_populates="evidence_details")
