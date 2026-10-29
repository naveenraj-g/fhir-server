from sqlalchemy import BigInteger, Column, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirAttachmentMixin, TenantAuditMixin


class DiagnosticReportPresentedForm(FhirAttachmentMixin, TenantAuditMixin, Base):
    """One entry of DiagnosticReport.presentedForm (0..* Attachment) —
    the full report as issued, e.g. a PDF. Whole row is the attachment,
    no prefix needed — this codebase's first dedicated 0..* Attachment
    child table (Practitioner.photo is the other; HealthcareService's
    is a 0..1 flattened group with its own hand-declared columns, see
    FhirAttachmentMixin's own docstring)."""

    __tablename__ = "diagnostic_report_presented_form"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    diagnostic_report_pk = Column(BigInteger, ForeignKey("diagnostic_report.id"), nullable=False, index=True)

    diagnostic_report = relationship("DiagnosticReportModel", back_populates="presented_forms")
