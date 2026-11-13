from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base


class LocationType(Base):
    """Search index for the `type` token parameter: one row per
    Location.type[].coding[] (plus one code-less row for a type with only
    `text`, so `type:text` still finds it) — same shape as
    OrganizationType. Derived from LocationModel.content — never read to
    build a response."""

    __tablename__ = "location_type"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    location_pk = Column(
        BigInteger, ForeignKey("location.id"), nullable=False, index=True
    )
    system = Column(String, nullable=True)
    code = Column(String, nullable=True, index=True)
    display_norm = Column(String, nullable=True)
    text_norm = Column(String, nullable=True)

    location = relationship("LocationModel", back_populates="types")
