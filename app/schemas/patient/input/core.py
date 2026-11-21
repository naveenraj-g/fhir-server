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
    FhirReferenceInput,
)

from .communication import PatientCommunicationInput
from .contact import PatientContactInput
from .link import PatientLinkInput

_EXAMPLE = {
    "resourceType": "Patient",
    "active": True,
    "gender": "male",
    "birthDate": "1974-12-25",
    "deceasedBoolean": False,
    "identifier": [
        {
            "use": "official",
            "system": "http://hospital.example.org/mrn",
            "value": "MRN-12345",
        }
    ],
    "name": [
        {
            "use": "official",
            "family": "Chalmers",
            "given": ["Peter", "James"],
            "prefix": ["Mr"],
        }
    ],
    "telecom": [{"system": "phone", "value": "555-1234", "use": "home"}],
    "address": [
        {
            "use": "home",
            "line": ["534 Erewhon St"],
            "city": "PleasantVille",
            "state": "Vic",
            "postalCode": "3999",
            "country": "AU",
        }
    ],
    "maritalStatus": {"coding": [{"code": "M", "display": "Married"}]},
    "contact": [
        {
            "relationship": [{"coding": [{"code": "N", "display": "Next-of-Kin"}]}],
            "name": {"family": "Chalmers", "given": ["Sarah"]},
            "telecom": [{"system": "phone", "value": "555-9876"}],
        }
    ],
    "communication": [
        {
            "language": {"coding": [{"code": "en", "display": "English"}]},
            "preferred": True,
        }
    ],
    "generalPractitioner": [{"reference": "Practitioner/30001"}],
    "managingOrganization": {"reference": "Organization/190001"},
}


class _PatientFields(FhirInputModel):
    """Every writable Patient element, in genuine FHIR R4 shape
    (https://www.hl7.org/fhir/R4/patient.html). Create and patch accept
    exactly the same fields — Patient has no element that is required at this
    layer (R4 requires `link.other`/`link.type`, `communication.language` and
    a `contact` to carry something, which base R4 validation enforces on the
    stored document).

    The validated body is stored whole (PatientModel.content), so any valid R4
    element is kept — including ones this model doesn't declare.
    Server-managed elements are ignored if sent: `id` (assigned from the
    patient_id sequence) and `meta` (audit/tenant data, stamped on at read
    time). org_id and created_by/updated_by come from the verified JWT
    (actor.org_id / actor.sub), never the body.

    The end-user a record belongs to (`user_id`, which scopes `/me`) is not a
    FHIR element and is not accepted here: it is set afterwards with
    `PUT /patients/{id}/user`, or at create time with `?link_me=true`."""

    resourceType: Literal["Patient"] | None = Field(
        None, description="Optional; if supplied it must be 'Patient'."
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries — validated by the profile pipeline, not here.",
    )
    identifier: list[FhirIdentifierInput] | None = Field(
        None, description="An identifier for this patient."
    )
    active: bool | None = Field(
        None, description="Whether this patient's record is in active use."
    )
    name: list[FhirHumanNameInput] | None = Field(
        None, description="A name associated with the patient."
    )
    telecom: list[FhirContactPointInput] | None = Field(
        None, description="A contact detail for the individual."
    )
    gender: AdministrativeGender | None = Field(
        None, description="male | female | other | unknown."
    )
    birthDate: str | None = Field(
        None,
        description="The date of birth for the individual (FHIR date: YYYY, YYYY-MM or YYYY-MM-DD).",
    )
    deceasedBoolean: bool | None = Field(
        None,
        description="Indicates if the individual is deceased or not (deceased[x] — send this or deceasedDateTime).",
    )
    deceasedDateTime: str | None = Field(
        None,
        description="Date and time of death (deceased[x] — send this or deceasedBoolean).",
    )
    address: list[FhirAddressInput] | None = Field(
        None, description="An address for the individual."
    )
    maritalStatus: FhirCodeableConceptInput | None = Field(
        None, description="Marital (civil) status of a patient."
    )
    multipleBirthBoolean: bool | None = Field(
        None,
        description="Whether patient is part of a multiple birth (multipleBirth[x] — send this or multipleBirthInteger).",
    )
    multipleBirthInteger: int | None = Field(
        None,
        description="Birth order of a multiple birth (multipleBirth[x] — send this or multipleBirthBoolean).",
    )
    photo: list[FhirAttachmentInput] | None = Field(
        None, description="Image of the patient."
    )
    contact: list[PatientContactInput] | None = Field(
        None,
        description="A contact party (e.g. guardian, partner, friend) for the patient.",
    )
    communication: list[PatientCommunicationInput] | None = Field(
        None,
        description="A language which may be used to communicate with the patient about his or her health.",
    )
    generalPractitioner: list[FhirReferenceInput] | None = Field(
        None,
        description="Patient's nominated primary care provider — Reference(Organization | Practitioner | PractitionerRole). A relative reference must exist in the caller's org (422 otherwise).",
    )
    managingOrganization: FhirReferenceInput | None = Field(
        None,
        description="Organization that is the custodian of the patient record — Reference(Organization). A relative 'Organization/<id>' reference must exist in the caller's org (422 otherwise).",
    )
    link: list[PatientLinkInput] | None = Field(
        None,
        description="Link to another patient resource that concerns the same actual person.",
    )


class PatientCreateSchema(_PatientFields):
    """POST body — a FHIR R4 Patient resource. Creates the patient and every
    supplied nested element atomically in one transaction."""

    model_config = {"json_schema_extra": {"example": _EXAMPLE}}


class PatientPatchSchema(_PatientFields):
    """PATCH body — a partial FHIR R4 Patient (merge-patch semantics on
    top-level elements). Only supplied elements are written; omitted ones are
    left untouched. A supplied element replaces the stored value wholesale — a
    list (even `[]`) replaces every existing entry, and `null` clears it."""

    model_config = {
        "json_schema_extra": {
            "example": {
                "telecom": [{"system": "phone", "value": "555-0000", "use": "mobile"}],
                "active": False,
            }
        }
    }
