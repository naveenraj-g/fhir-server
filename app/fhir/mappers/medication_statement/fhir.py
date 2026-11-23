"""MedicationStatementModel row -> FHIR R4 MedicationStatement. The only
read-side mapper.

The resource is stored whole in MedicationStatementModel.content (see the
model's docstring), so this doesn't rebuild anything from columns — see
app.fhir.mappers.content.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.mappers.content import content_resource

if TYPE_CHECKING:
    from app.models.medication_statement import MedicationStatementModel


def to_fhir_medication_statement(
    medication_statement: MedicationStatementModel,
) -> dict:
    return content_resource(
        "MedicationStatement",
        medication_statement.medication_statement_id,
        medication_statement,
    )
