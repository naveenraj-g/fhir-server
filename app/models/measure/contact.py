from sqlalchemy import BigInteger, Column, Enum, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.measure.enums import MeasureContactRole
from app.models.shared import FhirContactPointMixin, TenantAuditMixin


class MeasureContact(TenantAuditMixin, Base):
    """Measure contact details (contact, author, editor, reviewer, endorser)."""

    __tablename__ = "measure_contact"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    measure_pk = Column(
        BigInteger, ForeignKey("measure.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role = Column(
        Enum(MeasureContactRole, name="measure_contact_role"),
        nullable=False,
        index=True,
    )
    name = Column(String, nullable=True)

    measure = relationship("MeasureModel", back_populates="contacts")
    telecoms = relationship(
        "MeasureContactTelecom",
        back_populates="contact",
        cascade="all, delete-orphan",
    )


class MeasureContactTelecom(FhirContactPointMixin, TenantAuditMixin, Base):
    """One entry of ContactDetail.telecom (0..*)."""

    __tablename__ = "measure_contact_telecom"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    measure_contact_id = Column(
        BigInteger,
        ForeignKey("measure_contact.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    contact = relationship("MeasureContact", back_populates="telecoms")
