"""ProcedureModel row -> FHIR R4 Procedure. The only
read-side mapper.

The resource is stored whole in ProcedureModel.content (see the
model's docstring), so this doesn't rebuild anything from columns — see
app.fhir.mappers.content.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.mappers.content import content_resource

if TYPE_CHECKING:
    from app.models.procedure import ProcedureModel


def to_fhir_procedure(procedure: ProcedureModel) -> dict:
    return content_resource("Procedure", procedure.procedure_id, procedure)
