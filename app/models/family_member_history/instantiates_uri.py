from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base


class FamilyMemberHistoryInstantiatesUri(Base):
    """Search index for `instantiates-uri` (FamilyMemberHistory.instantiatesUri, 0..* uri):
    one row per URI. A `uri` search matches exactly (case-sensitive); `:below` matches
    stored URIs that start with the value and `:above` stored URIs that are a prefix of it.
    Derived from FamilyMemberHistoryModel.content — never read to build a response."""

    __tablename__ = "family_member_history_instantiates_uri"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    family_member_history_pk = Column(
        BigInteger, ForeignKey("family_member_history.id"), nullable=False, index=True
    )
    uri = Column(String, nullable=False, index=True)

    family_member_history = relationship(
        "FamilyMemberHistoryModel", back_populates="instantiates_uris"
    )
