from sqlalchemy import BigInteger, Column, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base

# The seven R4 targets of Group.member.entity.
MEMBER_TYPES = (
    "Patient",
    "Practitioner",
    "PractitionerRole",
    "Device",
    "Medication",
    "Substance",
    "Group",
)


class GroupMember(Base):
    """Search index for `member` (Group.member.entity, 0..* members, each with one entity
    Reference): one row per member whose entity has a `reference` or an `identifier`. Derived
    from GroupModel.content - never read to build a response.

    `reference_type` records which type a relative `Type/<id>` names - a plain string, not a
    Postgres enum, because the entity can be one of seven types (a search by bare id is
    ambiguous: `member=Type/id` or `:Type=id`).

      member             -> reference_type/reference_id or reference_reference
      member:identifier  -> reference_identifier_system/_value

    `period` and `inactive` live only in `content`."""

    __tablename__ = "group_member"
    __table_args__ = (
        Index("ix_group_member_type_id", "reference_type", "reference_id"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    group_pk = Column(BigInteger, ForeignKey("group.id"), nullable=False, index=True)
    reference_reference = Column(String, nullable=True)
    reference_type = Column(String, nullable=True)
    reference_id = Column(BigInteger, nullable=True)
    reference_identifier_system = Column(String, nullable=True)
    reference_identifier_value = Column(String, nullable=True)

    group = relationship("GroupModel", back_populates="members")
