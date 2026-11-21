from typing import Literal

from pydantic import Field

from app.schemas.fhir_input import (
    FhirCodeableConceptInput,
    FhirIdentifierInput,
    FhirInputModel,
    FhirPeriodInput,
    FhirReferenceInput,
)

StatusCode = Literal["partial", "completed", "entered-in-error", "health-unknown"]

_EXAMPLE = {
    "resourceType": "FamilyMemberHistory",
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/family-member-history-id",
            "value": "FMH-1001",
        }
    ],
    "status": "completed",
    "patient": {"reference": "Patient/10001"},
    "date": "2023-01-15T09:30:00Z",
    "name": "Mary Windsor",
    "relationship": {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/v3-RoleCode",
                "code": "MTH",
                "display": "mother",
            }
        ]
    },
    "sex": {
        "coding": [
            {
                "system": "http://hl7.org/fhir/administrative-gender",
                "code": "female",
                "display": "Female",
            }
        ]
    },
    "bornDate": "1950-03-12",
    "deceasedBoolean": False,
    "reasonCode": [
        {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": "160303001",
                    "display": "Family history of diabetes",
                }
            ]
        }
    ],
    "note": [{"text": "Mother has had type 2 diabetes since her forties."}],
    "condition": [
        {
            "code": {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "44054006",
                        "display": "Type 2 diabetes mellitus",
                    }
                ]
            },
            "outcome": {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "6736007",
                        "display": "Moderate",
                    }
                ]
            },
            "contributedToDeath": False,
            "onsetAge": {
                "value": 42,
                "unit": "yr",
                "system": "http://unitsofmeasure.org",
                "code": "a",
            },
        }
    ],
}


class FamilyMemberHistoryQuantityInput(FhirInputModel):
    """Age — a Quantity with a time unit."""

    value: float | int | None = Field(
        None, description="Numerical value (with implicit precision)."
    )
    comparator: Literal["<", "<=", ">=", ">"] | None = Field(
        None, description="< | <= | >= | > - how to understand the value."
    )
    unit: str | None = Field(None, description="Unit representation.")
    system: str | None = Field(
        None,
        description="System that defines coded unit form (usually http://unitsofmeasure.org).",
    )
    code: str | None = Field(None, description="Coded form of the unit.")


class FamilyMemberHistoryRangeInput(FhirInputModel):
    """Range — a low and a high Quantity."""

    low: FamilyMemberHistoryQuantityInput | None = Field(None, description="Low limit.")
    high: FamilyMemberHistoryQuantityInput | None = Field(
        None, description="High limit."
    )


class FamilyMemberHistoryAnnotationInput(FhirInputModel):
    """Annotation — a note with an author (a Reference or plain text) and a time."""

    authorReference: FhirReferenceInput | None = Field(
        None,
        description="Individual responsible for the annotation — Reference(Practitioner | PractitionerRole | Patient | RelatedPerson | Organization). A relative reference must exist in the caller's org (422 otherwise).",
    )
    authorString: str | None = Field(
        None, description="Individual responsible for the annotation, as plain text."
    )
    time: str | None = Field(
        None, description="When the annotation was made (a FHIR dateTime)."
    )
    text: str | None = Field(
        None, description="The annotation text, as markdown (required by R4)."
    )


class FamilyMemberHistoryConditionInput(FhirInputModel):
    """FamilyMemberHistory.condition — a condition that the related person had."""

    code: FhirCodeableConceptInput | None = Field(
        None, description="Condition suffered by relation (required by R4)."
    )
    outcome: FhirCodeableConceptInput | None = Field(
        None, description="Result of the condition for the family member."
    )
    contributedToDeath: bool | None = Field(
        None, description="Whether the condition contributed to the cause of death."
    )
    onsetAge: FamilyMemberHistoryQuantityInput | None = Field(
        None,
        description="When the condition first manifested (an Age). One of the onset[x] choices.",
    )
    onsetRange: FamilyMemberHistoryRangeInput | None = Field(
        None,
        description="When the condition first manifested (a Range). One of the onset[x] choices.",
    )
    onsetPeriod: FhirPeriodInput | None = Field(
        None,
        description="When the condition first manifested (a Period). One of the onset[x] choices.",
    )
    onsetString: str | None = Field(
        None,
        description="When the condition first manifested (a string). One of the onset[x] choices.",
    )
    note: list[FamilyMemberHistoryAnnotationInput] | None = Field(
        None, description="Extra information about condition."
    )


class _FamilyMemberHistoryFields(FhirInputModel):
    """Every writable FamilyMemberHistory element, in genuine FHIR R4 shape
    (https://www.hl7.org/fhir/R4/familymemberhistory.html). Create and patch accept
    exactly the same fields. R4 requires `status`, `patient` and `relationship`; that is
    enforced by base R4 validation of the stored document (the `java_validator` backend — the
    native structural check has no cardinality minimums), not by this model. R4 rules fhs-1
    (age[x] or born[x], not both) and fhs-2 (estimatedAge needs age[x]) are enforced the same
    way. A PATCH may omit them: it is merged onto the current resource before validating.

    The validated body is stored whole (FamilyMemberHistoryModel.content), so any valid
    R4 element is kept — including ones this model does not declare. Server-managed
    elements are ignored if sent: `id` (assigned from the family_member_history_id
    sequence) and `meta` (audit/tenant data, stamped on at read time). org_id and
    created_by/updated_by come from the verified JWT (actor.org_id / actor.sub),
    never the body. There is no user_id."""

    resourceType: Literal["FamilyMemberHistory"] | None = Field(
        None, description="Optional; if supplied it must be 'FamilyMemberHistory'."
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries — validated by the profile pipeline, not here.",
    )
    identifier: list[FhirIdentifierInput] | None = Field(
        None, description="External Id(s) for this record."
    )
    instantiatesCanonical: list[str] | None = Field(
        None,
        description="Instantiates FHIR protocol or definition — canonical URLs of PlanDefinition | Questionnaire | ActivityDefinition | Measure | OperationDefinition.",
    )
    instantiatesUri: list[str] | None = Field(
        None, description="Instantiates external protocol or definition (URIs)."
    )
    status: StatusCode | None = Field(
        None,
        description="partial | completed | entered-in-error | health-unknown (required by R4).",
    )
    dataAbsentReason: FhirCodeableConceptInput | None = Field(
        None, description="subject-unknown | withheld | unable-to-obtain | deferred."
    )
    patient: FhirReferenceInput | None = Field(
        None,
        description="Patient history is about — Reference(Patient) (required by R4). A relative 'Patient/<id>' reference must exist in the caller's org (422 otherwise).",
    )
    date: str | None = Field(
        None, description="When history was recorded or last updated (a FHIR dateTime)."
    )
    name: str | None = Field(None, description="The family member described.")
    relationship: FhirCodeableConceptInput | None = Field(
        None, description="Relationship to the subject (required by R4)."
    )
    sex: FhirCodeableConceptInput | None = Field(
        None, description="male | female | other | unknown."
    )
    bornPeriod: FhirPeriodInput | None = Field(
        None,
        description="(Approximate) date of birth (a Period). One of the born[x] choices.",
    )
    bornDate: str | None = Field(
        None,
        description="(Approximate) date of birth (a FHIR date). One of the born[x] choices.",
    )
    bornString: str | None = Field(
        None,
        description="(Approximate) date of birth (a string). One of the born[x] choices.",
    )
    ageAge: FamilyMemberHistoryQuantityInput | None = Field(
        None, description="(Approximate) age (an Age). One of the age[x] choices."
    )
    ageRange: FamilyMemberHistoryRangeInput | None = Field(
        None, description="(Approximate) age (a Range). One of the age[x] choices."
    )
    ageString: str | None = Field(
        None, description="(Approximate) age (a string). One of the age[x] choices."
    )
    estimatedAge: bool | None = Field(None, description="Age is estimated?")
    deceasedBoolean: bool | None = Field(
        None,
        description="Dead? How old/when? (a boolean). One of the deceased[x] choices.",
    )
    deceasedAge: FamilyMemberHistoryQuantityInput | None = Field(
        None,
        description="Dead? How old/when? (an Age). One of the deceased[x] choices.",
    )
    deceasedRange: FamilyMemberHistoryRangeInput | None = Field(
        None,
        description="Dead? How old/when? (a Range). One of the deceased[x] choices.",
    )
    deceasedDate: str | None = Field(
        None,
        description="Dead? How old/when? (a FHIR date). One of the deceased[x] choices.",
    )
    deceasedString: str | None = Field(
        None,
        description="Dead? How old/when? (a string). One of the deceased[x] choices.",
    )
    reasonCode: list[FhirCodeableConceptInput] | None = Field(
        None, description="Why was family member history performed?"
    )
    reasonReference: list[FhirReferenceInput] | None = Field(
        None,
        description="Why was family member history performed? — Reference(Condition | Observation | AllergyIntolerance | QuestionnaireResponse | DiagnosticReport | DocumentReference). A relative Condition, AllergyIntolerance or DiagnosticReport must exist in the caller's org (422 otherwise).",
    )
    note: list[FamilyMemberHistoryAnnotationInput] | None = Field(
        None, description="General note about related person."
    )
    condition: list[FamilyMemberHistoryConditionInput] | None = Field(
        None, description="Condition that the related person had."
    )


class FamilyMemberHistoryCreateSchema(_FamilyMemberHistoryFields):
    """POST body — a FHIR R4 FamilyMemberHistory resource."""

    model_config = {"json_schema_extra": {"example": _EXAMPLE}}


class FamilyMemberHistoryPatchSchema(_FamilyMemberHistoryFields):
    """PATCH body — a partial FHIR R4 FamilyMemberHistory (merge-patch semantics on
    top-level elements). Only supplied elements are written; omitted ones are left
    untouched. A supplied element replaces the stored value wholesale — a list
    (even `[]`) replaces every existing entry, an object such as `relationship` replaces
    the whole value, and `null` clears it."""

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "entered-in-error",
                "note": [{"text": "Recorded against the wrong patient."}],
            }
        }
    }
