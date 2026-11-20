"""EncounterModel row -> FHIR R4 Encounter. The only
read-side mapper.

The resource is stored whole in EncounterModel.content (see the
model's docstring), so this doesn't rebuild anything from columns — see
app.fhir.mappers.content.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.mappers.content import content_resource

if TYPE_CHECKING:
    from app.models.encounter import EncounterModel


def to_fhir_encounter(encounter: EncounterModel) -> dict:
    return content_resource("Encounter", encounter.encounter_id, encounter)
