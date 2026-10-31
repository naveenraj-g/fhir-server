from sqlalchemy import BigInteger, Column, Enum, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.enums import IdentifierUse
from app.models.patient.enums import PatientLinkOtherType, PatientLinkType
from app.models.shared import TenantAuditMixin


class PatientLink(TenantAuditMixin, Base):
    """Patient.link (0..* BackboneElement) child table.
    Links to a Patient or RelatedPerson resource that concerns the same actual individual."""

    __tablename__ = "patient_link"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    patient_pk = Column(
        BigInteger, ForeignKey("patient.id"), nullable=False, index=True
    )

    other_reference = Column(String, nullable=True)
    other_type = Column(
        Enum(PatientLinkOtherType, name="patient_link_other_type"),
        nullable=True,
    )
    other_id = Column(BigInteger, nullable=True, index=True)
    other_display = Column(String, nullable=True)

    other_identifier_system = Column(String, nullable=True)
    other_identifier_value = Column(String, nullable=True)
    other_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    other_identifier_type_text = Column(String, nullable=True)

    type = Column(
        Enum(PatientLinkType, name="patient_link_type"),
        nullable=True,
    )

    patient = relationship("PatientModel", back_populates="links")
