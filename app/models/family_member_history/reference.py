from sqlalchemy import BigInteger, Column, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base

# The one parameter held in FamilyMemberHistoryReference, the element it reads and the
# resource types that element can name (R4: instantiatesCanonical -> canonical URLs of
# PlanDefinition | Questionnaire | ActivityDefinition | Measure | OperationDefinition).
REFERENCE_PARAMS = {"instantiates-canonical": "instantiatesCanonical"}
REFERENCE_TYPES = {
    "instantiates-canonical": (
        "PlanDefinition",
        "Questionnaire",
        "ActivityDefinition",
        "Measure",
        "OperationDefinition",
    ),
}


class FamilyMemberHistoryReference(Base):
    """Search index for `instantiates-canonical` (FamilyMemberHistory.instantiatesCanonical,
    0..* canonical URLs): one row per URL. `param` says which search parameter the row
    belongs to (see REFERENCE_PARAMS). Derived from FamilyMemberHistoryModel.content —
    never read to build a response.

    `reference_type` records which resource type a relative `Type/<id>` names — a plain
    string, not a Postgres enum (the element has several targets, so a search by bare id is
    ambiguous). A canonical is usually just the raw string; a versioned `url|1.0` is matched
    by the unversioned `url` too.

      instantiates-canonical -> reference_type/reference_id (a relative Type/<id>) or
                                reference_reference (the raw string, for a canonical URL)

    No ForeignKey on `reference_id` and no UniqueConstraint: R4 does not forbid listing the
    same canonical twice."""

    __tablename__ = "family_member_history_reference"
    __table_args__ = (
        Index(
            "ix_family_member_history_reference_param_type_id",
            "param",
            "reference_type",
            "reference_id",
        ),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    family_member_history_pk = Column(
        BigInteger, ForeignKey("family_member_history.id"), nullable=False, index=True
    )
    param = Column(String, nullable=False)
    reference_reference = Column(String, nullable=True)
    reference_type = Column(String, nullable=True)
    reference_id = Column(BigInteger, nullable=True)

    family_member_history = relationship(
        "FamilyMemberHistoryModel", back_populates="references"
    )
