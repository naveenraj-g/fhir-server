"""HealthcareServiceModel row -> FHIR R4 HealthcareService. The only
read-side mapper.

The resource is stored whole in HealthcareServiceModel.content (see the
model's docstring), so this doesn't rebuild anything from columns — see
app.fhir.mappers.content.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.mappers.content import content_resource

if TYPE_CHECKING:
    from app.models.healthcare_service import HealthcareServiceModel


def to_fhir_healthcare_service(service: HealthcareServiceModel) -> dict:
    return content_resource("HealthcareService", service.healthcare_service_id, service)
