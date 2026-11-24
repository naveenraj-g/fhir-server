from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base


class CommunicationInstantiatesUri(Base):
    """Search index for `instantiates-uri` (Communication.instantiatesUri, 0..* uri): one row per
    URI. A `uri` search matches exactly (case-sensitive); `:below` matches stored URIs that start
    with the value and `:above` stored URIs that are a prefix of it. Derived from
    CommunicationModel.content - never read to build a response."""

    __tablename__ = "communication_instantiates_uri"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    communication_pk = Column(
        BigInteger, ForeignKey("communication.id"), nullable=False, index=True
    )
    uri = Column(String, nullable=False, index=True)

    communication = relationship(
        "CommunicationModel", back_populates="instantiates_uris"
    )
