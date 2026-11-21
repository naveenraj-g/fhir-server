"""DiagnosticReportModel row -> FHIR R4 DiagnosticReport. The only
read-side mapper.

The resource is stored whole in DiagnosticReportModel.content (see the
model's docstring), so this doesn't rebuild anything from columns — see
app.fhir.mappers.content.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.mappers.content import content_resource

if TYPE_CHECKING:
    from app.models.diagnostic_report import DiagnosticReportModel


def to_fhir_diagnostic_report(diagnostic_report: DiagnosticReportModel) -> dict:
    return content_resource(
        "DiagnosticReport", diagnostic_report.diagnostic_report_id, diagnostic_report
    )
