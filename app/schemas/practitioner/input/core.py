from typing import Literal

from pydantic import Field

from app.schemas.enums import AdministrativeGender
from app.schemas.fhir_input import (
    FhirAddressInput,
    FhirAttachmentInput,
    FhirCodeableConceptInput,
    FhirContactPointInput,
    FhirHumanNameInput,
    FhirIdentifierInput,
    FhirInputModel,
)

from .qualification import PractitionerQualificationInput

_EXAMPLE = {
    "resourceType": "Practitioner",
    "active": True,
    "gender": "female",
    "birthDate": "1980-05-15",
    "identifier": [
        {
            "use": "official",
            "system": "http://hl7.org/fhir/sid/us-npi",
            "value": "9941339108",
        }
    ],
    "name": [
        {"use": "official", "family": "Careful", "given": ["Adam"], "prefix": ["Dr"]}
    ],
    "telecom": [{"system": "phone", "value": "555-9988", "use": "work"}],
    "address": [
        {
            "use": "work",
            "line": ["534 Erewhon St"],
            "city": "PleasantVille",
            "state": "Vic",
            "postalCode": "3999",
        }
    ],
    "photo": [{"url": "https://fhir-server.dev/fhir/assets/photo.png"}],
    "qualification": [
        {
            "code": {
                "coding": [{"code": "BS", "display": "Bachelor of Science"}],
                "text": "Bachelor of Science",
            },
            "issuer": {"reference": "Organization/190001"},
        }
    ],
    "communication": [{"coding": [{"code": "en", "display": "English"}]}],
}


class _PractitionerFields(FhirInputModel):
    """Every writable Practitioner element, in genuine FHIR R4 shape
    (https://www.hl7.org/fhir/R4/practitioner.html). Create and patch accept
    exactly the same fields — Practitioner has no element that is required
    at this layer.

    The validated body is stored whole (PractitionerModel.content), so any
    valid R4 element is kept — including ones this model doesn't declare.
    Server-managed elements are ignored if sent: `id` (assigned from the
    practitioner_id sequence) and `meta` (audit/tenant data, stamped on at
    read time). org_id and created_by/updated_by come from the verified JWT
    (actor.org_id / actor.sub), never the body.

    The end-user a record belongs to (`user_id`, which scopes `/me`) is not
    a FHIR element and is not accepted here: it is set afterwards with
    `PUT /practitioners/{id}/user`."""

    resourceType: Literal["Practitioner"] | None = Field(
        None, description="Optional; if supplied it must be 'Practitioner'."
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries — validated by the profile pipeline, not here.",
    )
    identifier: list[FhirIdentifierInput] | None = Field(
        None, description="An identifier for the person as this agent."
    )
    active: bool | None = Field(
        None, description="Whether this practitioner's record is in active use."
    )
    name: list[FhirHumanNameInput] | None = Field(
        None, description="The name(s) associated with the practitioner."
    )
    telecom: list[FhirContactPointInput] | None = Field(
        None, description="A contact detail for the practitioner (that apply to all roles)."
    )
    address: list[FhirAddressInput] | None = Field(
        None, description="Address(es) of the practitioner that are not role specific."
    )
    gender: AdministrativeGender | None = Field(
        None, description="male | female | other | unknown."
    )
    birthDate: str | None = Field(
        None, description="The date on which the practitioner was born (FHIR date: YYYY, YYYY-MM or YYYY-MM-DD)."
    )
    photo: list[FhirAttachmentInput] | None = Field(
        None, description="Image of the person."
    )
    qualification: list[PractitionerQualificationInput] | None = Field(
        None, description="Certification, licenses, or training pertaining to the provision of care."
    )
    communication: list[FhirCodeableConceptInput] | None = Field(
        None, description="A language the practitioner can use in patient communication."
    )


class PractitionerCreateSchema(_PractitionerFields):
    """POST body — a FHIR R4 Practitioner resource. Creates the
    practitioner and every supplied nested element atomically in one
    transaction."""

    model_config = {"json_schema_extra": {"example": _EXAMPLE}}


class PractitionerPatchSchema(_PractitionerFields):
    """PATCH body — a partial FHIR R4 Practitioner (merge-patch semantics on
    top-level elements). Only supplied elements are written; omitted ones
    are left untouched. A supplied element replaces the stored value
    wholesale — a list (even `[]`) replaces every existing entry, and `null`
    clears it."""

    model_config = {
        "json_schema_extra": {
            "example": {
                "telecom": [{"system": "phone", "value": "555-0000", "use": "work"}],
                "active": False,
            }
        }
    }
