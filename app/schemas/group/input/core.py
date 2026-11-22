from typing import Literal

from pydantic import Field

from app.schemas.fhir_input import (
    FhirCodeableConceptInput,
    FhirIdentifierInput,
    FhirInputModel,
    FhirPeriodInput,
    FhirReferenceInput,
)

# GroupType (the required binding of Group.type).
TypeCode = Literal[
    "person", "animal", "practitioner", "device", "medication", "substance"
]

_EXAMPLE = {
    "resourceType": "Group",
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/group-id",
            "value": "GRP-1001",
        }
    ],
    "active": True,
    "type": "person",
    "actual": True,
    "code": {
        "coding": [
            {
                "system": "http://snomed.info/sct",
                "code": "385093006",
                "display": "Community",
            }
        ]
    },
    "name": "Diabetes cohort",
    "quantity": 2,
    "managingEntity": {"reference": "Organization/190001"},
    "characteristic": [
        {
            "code": {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": "8302-2",
                        "display": "Body height",
                    }
                ]
            },
            "valueRange": {
                "low": {"value": 150, "unit": "cm"},
                "high": {"value": 190, "unit": "cm"},
            },
            "exclude": False,
        }
    ],
    "member": [
        {"entity": {"reference": "Patient/10001"}, "period": {"start": "2023-01-01"}},
        {"entity": {"reference": "Patient/10002"}, "inactive": False},
    ],
}


class GroupQuantityInput(FhirInputModel):
    """Quantity - a measured amount with an optional comparator."""

    value: float | int | None = Field(
        None, description="Numerical value (with implicit precision)."
    )
    comparator: Literal["<", "<=", ">=", ">"] | None = Field(
        None, description="How the value should be understood: < | <= | >= | >."
    )
    unit: str | None = Field(None, description="Unit representation.")
    system: str | None = Field(
        None,
        description="System that defines coded unit form (usually http://unitsofmeasure.org).",
    )
    code: str | None = Field(None, description="Coded form of the unit.")


class GroupRangeInput(FhirInputModel):
    """Range - a set of values bounded by low and high."""

    low: GroupQuantityInput | None = Field(None, description="Low limit.")
    high: GroupQuantityInput | None = Field(None, description="High limit.")


class GroupCharacteristicInput(FhirInputModel):
    """Group.characteristic - include / exclude group members by trait."""

    code: FhirCodeableConceptInput | None = Field(
        None,
        description="Kind of characteristic (required by R4). Searched by `characteristic`.",
    )
    valueCodeableConcept: FhirCodeableConceptInput | None = Field(
        None,
        description="Value held by characteristic (a CodeableConcept). One of the value[x] choices (required by R4); searched by `value`.",
    )
    valueBoolean: bool | None = Field(
        None,
        description="Value held by characteristic (a boolean). One of the value[x] choices; searched by `value`.",
    )
    valueQuantity: GroupQuantityInput | None = Field(
        None,
        description="Value held by characteristic (a Quantity). One of the value[x] choices.",
    )
    valueRange: GroupRangeInput | None = Field(
        None,
        description="Value held by characteristic (a Range). One of the value[x] choices.",
    )
    valueReference: FhirReferenceInput | None = Field(
        None,
        description="Value held by characteristic (a Reference to any resource). One of the value[x] choices. A relative reference to a rebuilt resource must exist in the caller's org (422 otherwise).",
    )
    exclude: bool | None = Field(
        None,
        description="Group includes or excludes (required by R4). Searched by `exclude`.",
    )
    period: FhirPeriodInput | None = Field(
        None, description="Period over which characteristic is tested."
    )


class GroupMemberInput(FhirInputModel):
    """Group.member - who or what is in the group."""

    entity: FhirReferenceInput | None = Field(
        None,
        description="Reference to the group member (required by R4) - Reference(Patient | Practitioner | PractitionerRole | Device | Medication | Substance | Group). A relative Patient, Practitioner, PractitionerRole, Medication or Group must exist in the caller's org (422 otherwise); Device and Substance are stored as sent. Searched by `member`.",
    )
    period: FhirPeriodInput | None = Field(
        None, description="Period member belonged to the group."
    )
    inactive: bool | None = Field(None, description="If member is no longer in group.")


class _GroupFields(FhirInputModel):
    """Every writable Group element, in genuine FHIR R4 shape
    (https://www.hl7.org/fhir/R4/group.html). Create and patch accept exactly the same fields.
    R4 requires `type` and `actual` (and rule grp-1: `member` only if `actual` is true), but
    those minimums are enforced by the base-R4 validator (`java_validator` backend), not by
    this model - so a PATCH can send any subset.

    The validated body is stored whole (GroupModel.content), so any valid R4 element is kept -
    including ones this model does not declare. Server-managed elements are ignored if sent:
    `id` (assigned from the group_id sequence) and `meta` (audit/tenant data, stamped on at
    read time). org_id and created_by/updated_by come from the verified JWT (actor.org_id /
    actor.sub), never the body. There is no user_id."""

    resourceType: Literal["Group"] | None = Field(
        None, description="Optional; if supplied it must be 'Group'."
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries - validated by the profile pipeline, not here.",
    )
    identifier: list[FhirIdentifierInput] | None = Field(None, description="Unique id.")
    active: bool | None = Field(
        None, description="Whether this group's record is in active use."
    )
    type: TypeCode | None = Field(
        None,
        description="person | animal | practitioner | device | medication | substance (required by R4).",
    )
    actual: bool | None = Field(
        None, description="Descriptive (false) or actual (true) (required by R4)."
    )
    code: FhirCodeableConceptInput | None = Field(
        None, description="Kind of Group members. Searched by `code`."
    )
    name: str | None = Field(None, description="Label for Group.")
    quantity: int | None = Field(None, ge=0, description="Number of members.")
    managingEntity: FhirReferenceInput | None = Field(
        None,
        description="Entity that is the custodian of the Group's definition - Reference(Organization | RelatedPerson | Practitioner | PractitionerRole). A relative reference must exist in the caller's org (422 otherwise).",
    )
    characteristic: list[GroupCharacteristicInput] | None = Field(
        None, description="Include / Exclude group members by Trait."
    )
    member: list[GroupMemberInput] | None = Field(
        None, description="Who or what is in group."
    )


class GroupCreateSchema(_GroupFields):
    """POST body - a FHIR R4 Group resource."""

    model_config = {"json_schema_extra": {"example": _EXAMPLE}}


class GroupPatchSchema(_GroupFields):
    """PATCH body - a partial FHIR R4 Group (merge-patch semantics on top-level elements). Only
    supplied elements are written; omitted ones are left untouched. A supplied element replaces
    the stored value wholesale - a list (even `[]`) replaces every existing entry and `null`
    clears an element."""

    model_config = {
        "json_schema_extra": {
            "example": {
                "active": False,
                "name": "Retired cohort",
                "member": [{"entity": {"reference": "Patient/10001"}}],
            }
        }
    }
