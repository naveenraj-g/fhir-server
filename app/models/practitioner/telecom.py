from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base


class PractitionerTelecom(Base):
    """Search index for `telecom`, `phone` and `email` (0..*): one row per
    Practitioner.telecom that has a value. Derived from
    PractitionerModel.content — never read to build a response.

    R4 searches a ContactPoint as a token: the code is matched against
    `value`, the optional system part of `system|code` against `use`.
    `phone` / `email` additionally require `system` to be that kind.
    No row for a ContactPoint with no value."""

    __tablename__ = "practitioner_telecom"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    practitioner_pk = Column(
        BigInteger, ForeignKey("practitioner.id"), nullable=False, index=True
    )
    system = Column(String, nullable=True)
    value = Column(String, nullable=True, index=True)
    use = Column(String, nullable=True)

    practitioner = relationship("PractitionerModel", back_populates="telecoms")
