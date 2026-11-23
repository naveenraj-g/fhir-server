from sqlalchemy import BigInteger, Column, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base

# Which search parameter an EpisodeOfCareReference row feeds, the EpisodeOfCare element it is read
# from, and the resource type that element points at (R4: diagnosis.condition -> Condition;
# referralRequest -> ServiceRequest).
REFERENCE_PARAMS = {
    "condition": "diagnosis.condition",
    "incoming-referral": "referralRequest",
}
REFERENCE_TYPES = {
    "condition": ("Condition",),
    "incoming-referral": ("ServiceRequest",),
}


class EpisodeOfCareReference(Base):
    """Search index for the two 0..* reference parameters `condition` (every
    `diagnosis.condition`) and `incoming-referral` (every `referralRequest`): one row per
    Reference that has a value (one with only `display` cannot be matched by a reference search).
    `param` says which search parameter the row belongs to (see REFERENCE_PARAMS). Derived from
    EpisodeOfCareModel.content - never read to build a response.

    `reference_type` records which resource type a relative `Type/<id>` names - a plain string,
    not a Postgres enum. Each parameter has one target, so a bare id works.

      <param>             -> reference_type/reference_id (a relative Type/<id>) or
                             reference_reference (the raw string, for an absolute URL)
      <param>:identifier  -> reference_identifier_system/_value

    No ForeignKey on `reference_id` (the public id of another resource) and no UniqueConstraint:
    R4 does not forbid listing the same reference twice."""

    __tablename__ = "episode_of_care_reference"
    __table_args__ = (
        Index(
            "ix_episode_of_care_reference_param_type_id",
            "param",
            "reference_type",
            "reference_id",
        ),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    episode_of_care_pk = Column(
        BigInteger, ForeignKey("episode_of_care.id"), nullable=False, index=True
    )
    param = Column(String, nullable=False)
    reference_reference = Column(String, nullable=True)
    reference_type = Column(String, nullable=True)
    reference_id = Column(BigInteger, nullable=True)
    reference_identifier_system = Column(String, nullable=True)
    reference_identifier_value = Column(String, nullable=True)

    episode_of_care = relationship("EpisodeOfCareModel", back_populates="references")
