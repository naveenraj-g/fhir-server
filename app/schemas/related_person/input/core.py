from typing import Literal

from pydantic import Field

from app.schemas.fhir_input import (
    FhirAddressInput,
    FhirAttachmentInput,
    FhirCodeableConceptInput,
    FhirContactPointInput,
    FhirHumanNameInput,
    FhirIdentifierInput,
    FhirInputModel,
    FhirPeriodInput,
    FhirReferenceInput,
)

GenderCode = Literal["male", "female", "other", "unknown"]

_EXAMPLE = {
    "resourceType": "RelatedPerson",
    "identifier": [{"system": "https://fhir-server.dev/fhir/identifier-system/related-person-id", "value": "RP-1001"}],
    "active": True,
    "patient": {"reference": "Patient/10001"},
    "relationship": [
        {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v3-RoleCode", "code": "MTH", "display": "mother"}]}
    ],
    "name": [{"use": "official", "family": "Windsor", "given": ["Mary"]}],
    "telecom": [{"system": "phone", "value": "555-9988", "use": "mobile"}],
    "gender": "female",
    "birthDate": "1965-04-12",
    "address": [{"use": "home", "line": ["1 Main St"], "city": "Boston", "state": "MA", "postalCode": "02110"}],
    "communication": [{"language": {"coding": [{"code": "en"}]}, "preferred": True}],
}


class RelatedPersonCommunicationInput(FhirInputModel):
    """RelatedPerson.communication — a language the person can be communicated with."""

    language: FhirCodeableConceptInput | None = Field(None, description="The language which can be used to communicate with the related person (required by R4).")
    preferred: bool | None = Field(None, description="Language preference indicator.")


class _RelatedPersonFields(FhirInputModel):
    """Every writable RelatedPerson element, in genuine FHIR R4 shape
    (https://www.hl7.org/fhir/R4/relatedperson.html). Create and patch accept
    exactly the same fields. R4 requires `patient`; that is enforced by base R4
    validation of the stored document (the `java_validator` backend — the native
    structural check has no cardinality minimums), not by this model. A PATCH may
    omit it: it is merged onto the current resource before validating.

    The validated body is stored whole (RelatedPersonModel.content), so any valid
    R4 element is kept — including ones this model does not declare.
    Server-managed elements are ignored if sent: `id` (assigned from the
    related_person_id sequence) and `meta` (audit/tenant data, stamped on at read
    time). org_id and created_by/updated_by come from the verified JWT
    (actor.org_id / actor.sub), never the body. There is no user_id."""

    resourceType: Literal["RelatedPerson"] | None = Field(None, description="Optional; if supplied it must be 'RelatedPerson'.")
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries — validated by the profile pipeline, not here.",
    )
    identifier: list[FhirIdentifierInput] | None = Field(None, description="A human identifier for this person.")
    active: bool | None = Field(None, description="Whether this related person record is in active use.")
    patient: FhirReferenceInput | None = Field(
        None,
        description="The patient this person is related to — Reference(Patient) (required by R4). A relative 'Patient/<id>' reference must exist in the caller's org (422 otherwise).",
    )
    relationship: list[FhirCodeableConceptInput] | None = Field(None, description="The nature of the relationship (e.g. mother, guardian, emergency contact).")
    name: list[FhirHumanNameInput] | None = Field(None, description="A name associated with the person.")
    telecom: list[FhirContactPointInput] | None = Field(None, description="A contact detail for the person.")
    gender: GenderCode | None = Field(None, description="male | female | other | unknown.")
    birthDate: str | None = Field(None, description="The date on which the related person was born (a FHIR date; may be partial: YYYY, YYYY-MM, YYYY-MM-DD).")
    address: list[FhirAddressInput] | None = Field(None, description="Address where the related person can be contacted or visited.")
    photo: list[FhirAttachmentInput] | None = Field(None, description="Image of the person.")
    period: FhirPeriodInput | None = Field(None, description="Period of time that this relationship is considered valid.")
    communication: list[RelatedPersonCommunicationInput] | None = Field(None, description="A language which may be used to communicate with about the patient health.")


class RelatedPersonCreateSchema(_RelatedPersonFields):
    """POST body — a FHIR R4 RelatedPerson resource."""

    model_config = {"json_schema_extra": {"example": _EXAMPLE}}


class RelatedPersonPatchSchema(_RelatedPersonFields):
    """PATCH body — a partial FHIR R4 RelatedPerson (merge-patch semantics on
    top-level elements). Only supplied elements are written; omitted ones are
    left untouched. A supplied element replaces the stored value wholesale — a
    list (even `[]`) replaces every existing entry, an object such as `period`
    replaces the whole value, and `null` clears it."""

    model_config = {"json_schema_extra": {"example": {"active": False, "telecom": [{"system": "phone", "value": "555-0000"}]}}}
