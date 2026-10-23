from sqlalchemy import BigInteger, Column, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirAttachmentMixin, TenantAuditMixin

# ---------------------------------------------------------------------------
# photo (0..*) Attachment child table — unlike HealthcareService.photo
# (0..1, flattened on the main table), Practitioner.photo is genuinely 0..*
# per R4, so it gets a real child table.
# ---------------------------------------------------------------------------


class PractitionerPhoto(FhirAttachmentMixin, TenantAuditMixin, Base):
    __tablename__ = "practitioner_photo"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    practitioner_pk = Column(
        BigInteger, ForeignKey("practitioner.id"), nullable=False, index=True
    )

    practitioner = relationship("PractitionerModel", back_populates="photos")
