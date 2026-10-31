from sqlalchemy import BigInteger, Column, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class FlagCodeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Flag.code.coding (0..*). Flag.code itself is 1..1."""

    __tablename__ = "flag_code_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    flag_pk = Column(
        BigInteger, ForeignKey("flag.id"), nullable=False, index=True
    )

    flag = relationship("FlagModel", back_populates="code_codings")
