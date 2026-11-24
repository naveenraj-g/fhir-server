"""MeasureReportModel row -> FHIR R4 MeasureReport. The only
read-side mapper.

The resource is stored whole in MeasureReportModel.content (see the
model's docstring), so this doesn't rebuild anything from columns — see
app.fhir.mappers.content.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.mappers.content import content_resource

if TYPE_CHECKING:
    from app.models.measure_report import MeasureReportModel


def to_fhir_measure_report(
    measure_report: MeasureReportModel,
) -> dict:
    return content_resource(
        "MeasureReport",
        measure_report.measure_report_id,
        measure_report,
    )
