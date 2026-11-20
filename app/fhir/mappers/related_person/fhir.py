"""RelatedPersonModel row -> FHIR R4 RelatedPerson. The only
read-side mapper.

The resource is stored whole in RelatedPersonModel.content (see the
model's docstring), so this doesn't rebuild anything from columns — see
app.fhir.mappers.content.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.mappers.content import content_resource

if TYPE_CHECKING:
    from app.models.related_person import RelatedPersonModel


def to_fhir_related_person(related_person: RelatedPersonModel) -> dict:
    return content_resource("RelatedPerson", related_person.related_person_id, related_person)
