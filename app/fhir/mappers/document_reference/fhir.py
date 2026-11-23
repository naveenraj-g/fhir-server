"""DocumentReferenceModel row -> FHIR R4 DocumentReference. The only
read-side mapper.

The resource is stored whole in DocumentReferenceModel.content (see the
model's docstring), so this doesn't rebuild anything from columns — see
app.fhir.mappers.content.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.mappers.content import content_resource

if TYPE_CHECKING:
    from app.models.document_reference import DocumentReferenceModel


def to_fhir_document_reference(document_reference: DocumentReferenceModel) -> dict:
    return content_resource("DocumentReference", document_reference.document_reference_id, document_reference)
