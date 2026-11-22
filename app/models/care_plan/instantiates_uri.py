from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base


class CarePlanInstantiatesUri(Base):
    """Search index for `instantiates-uri` (CarePlan.instantiatesUri, 0..* uri):
    one row per URI. A `uri` search matches exactly (case-sensitive); `:below`
    matches stored URIs that start with the value and `:above` stored URIs that
    are a prefix of it. Derived from CarePlanModel.content — never read to build
    a response."""

    __tablename__ = "care_plan_instantiates_uri"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    care_plan_pk = Column(
        BigInteger, ForeignKey("care_plan.id"), nullable=False, index=True
    )
    uri = Column(String, nullable=False, index=True)

    care_plan = relationship("CarePlanModel", back_populates="instantiates_uris")
