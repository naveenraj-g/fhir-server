from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import FHIRBase as Base
from app.schemas.enums import HumanNameUse


class PractitionerName(Base):
    __tablename__ = "practitioner_name"

    id = Column(Integer, primary_key=True, autoincrement=True)
    practitioner_id = Column(
        BigInteger, ForeignKey("practitioner.id"), nullable=False, index=True
    )
    org_id = Column(String, nullable=False)

    use = Column(Enum(HumanNameUse, name="human_name_use"), nullable=True)
    text = Column(String, nullable=True)
    family = Column(String, nullable=True)
    given = Column(Text, nullable=True)  # comma-separated
    prefix = Column(Text, nullable=True)  # comma-separated
    suffix = Column(Text, nullable=True)  # comma-separated
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, nullable=False)
    updated_by = Column(String, nullable=True)

    practitioner = relationship("PractitionerModel", back_populates="names")
