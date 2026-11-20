from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base


class ImmunizationProtocol(Base):
    """Search index for `series` (Immunization.protocolApplied.series, 0..1 per
    protocol): one row per protocolApplied with a series. Derived from
    ImmunizationModel.content — never read to build a response.

      series  -> series (as written, for :exact) / series_norm (accents stripped,
                 case-folded, for the default starts-with and :contains)

    The rest of protocolApplied (`authority`, `doseNumber[x]`, `seriesDoses[x]`) lives
    only in `content`; its `targetDisease` is in ImmunizationToken."""

    __tablename__ = "immunization_protocol"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    immunization_pk = Column(BigInteger, ForeignKey("immunization.id"), nullable=False, index=True)
    series = Column(String, nullable=True)
    series_norm = Column(String, nullable=True, index=True)

    immunization = relationship("ImmunizationModel", back_populates="protocols")
