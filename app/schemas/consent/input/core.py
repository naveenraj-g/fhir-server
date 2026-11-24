from typing import Literal

from pydantic import Field

from app.schemas.fhir_input import (
    FhirAttachmentInput,
    FhirCodeableConceptInput,
    FhirIdentifierInput,
    FhirInputModel,
    FhirPeriodInput,
    FhirReferenceInput,
)

# ConsentState (the required binding of Consent.status).
StatusCode = Literal[
    "draft", "proposed", "active", "rejected", "inactive", "entered-in-error"
]
# ConsentProvisionType / ConsentDataMeaning (the required bindings of provision.type and
# provision.data.meaning).
ProvisionType = Literal["deny", "permit"]
DataMeaning = Literal["instance", "related", "dependents", "authoredby"]

_EXAMPLE = {
    "resourceType": "Consent",
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/consent-id",
            "value": "C-1",
        }
    ],
    "status": "active",
    "scope": {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/consentscope",
                "code": "patient-privacy",
            }
        ]
    },
    "category": [{"coding": [{"system": "http://loinc.org", "code": "59284-0"}]}],
    "patient": {"reference": "Patient/10001"},
    "dateTime": "2026-01-15T09:00:00Z",
    "performer": [{"reference": "Patient/10001"}],
    "organization": [{"reference": "Organization/190001"}],
    "policyRule": {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "code": "OPTIN",
            }
        ]
    },
    "provision": {
        "type": "permit",
        "period": {"start": "2026-01-15", "end": "2027-01-14"},
        "actor": [
            {
                "role": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v3-ParticipationType",
                            "code": "IRCP",
                        }
                    ]
                },
                "reference": {"reference": "Practitioner/30001"},
            }
        ],
        "action": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/consentaction",
                        "code": "access",
                    }
                ]
            }
        ],
    },
}


class ConsentPolicyInput(FhirInputModel):
    """Consent.policy - policies covered by this consent."""

    authority: str | None = Field(
        None, description="Enforcement source for policy (a uri)."
    )
    uri: str | None = Field(
        None, description="Specific policy covered by this consent (a uri)."
    )


class ConsentVerificationInput(FhirInputModel):
    """Consent.verification - whether the consent was verified."""

    verified: bool | None = Field(
        None, description="Has been verified (required by R4)."
    )
    verifiedWith: FhirReferenceInput | None = Field(
        None, description="Person who verified - Reference(Patient | RelatedPerson)."
    )
    verificationDate: str | None = Field(
        None, description="When consent verified (a FHIR dateTime)."
    )


class ConsentProvisionActorInput(FhirInputModel):
    """Consent.provision.actor - who the rule applies to."""

    role: FhirCodeableConceptInput | None = Field(
        None, description="How the actor is involved (required by R4)."
    )
    reference: FhirReferenceInput | None = Field(
        None,
        description="Resource for the actor (or group, by role) - Reference(Device | Group | CareTeam | Organization | Patient | Practitioner | RelatedPerson | PractitionerRole) (required by R4). Searched by `actor`.",
    )


class ConsentProvisionDataInput(FhirInputModel):
    """Consent.provision.data - data controlled by this rule."""

    meaning: DataMeaning | None = Field(
        None,
        description="instance | related | dependents | authoredby (required by R4).",
    )
    reference: FhirReferenceInput | None = Field(
        None,
        description="The actual data reference - Reference(Any) (required by R4). Searched by `data`.",
    )


class ConsentProvisionInput(FhirInputModel):
    """Consent.provision - constraints to the base Consent.policyRule, nested recursively through
    `provision.provision`. The search parameters read the top-level provision only."""

    type: ProvisionType | None = Field(None, description="deny | permit.")
    period: FhirPeriodInput | None = Field(
        None, description="Timeframe for this rule. Searched by `period`."
    )
    actor: list[ConsentProvisionActorInput] | None = Field(
        None, description="Who|what controlled by this rule (or group, by role)."
    )
    action: list[FhirCodeableConceptInput] | None = Field(
        None, description="Actions controlled by this rule. Searched by `action`."
    )
    securityLabel: list[dict] | None = Field(
        None,
        description="Security Labels that define affected resources (Codings). Searched by `security-label`.",
    )
    purpose: list[dict] | None = Field(
        None,
        description="Context of activities covered by this rule (Codings). Searched by `purpose`.",
    )
    class_: list[dict] | None = Field(
        None,
        alias="class",
        description="e.g. Resource Type, Profile, CDA, etc. (Codings).",
    )
    code: list[FhirCodeableConceptInput] | None = Field(
        None, description="e.g. LOINC or SNOMED CT code, etc. in the content."
    )
    dataPeriod: FhirPeriodInput | None = Field(
        None, description="Timeframe for data controlled by this rule."
    )
    data: list[ConsentProvisionDataInput] | None = Field(
        None, description="Data controlled by this rule."
    )
    provision: list[dict] | None = Field(
        None, description="Nested Exception Rules (the same shape, recursively)."
    )


class _ConsentFields(FhirInputModel):
    """Every writable Consent element, in genuine FHIR R4 shape
    (https://www.hl7.org/fhir/R4/consent.html). Create and patch accept exactly the same fields.
    R4 requires `status`, `scope` and `category`; the native validator checks `scope` and
    `category` (a missing primitive `status` is only rejected by the `java_validator` backend,
    along with rules ppc-1..ppc-5).

    The validated body is stored whole (ConsentModel.content), so any valid R4 element is kept -
    including ones this model does not declare. Server-managed elements are ignored if sent: `id`
    (assigned from the consent_id sequence) and `meta` (audit/tenant data, stamped on at read
    time). org_id and created_by/updated_by come from the verified JWT (actor.org_id /
    actor.sub), never the body. There is no user_id."""

    resourceType: Literal["Consent"] | None = Field(
        None, description="Optional; if supplied it must be 'Consent'."
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries - validated by the profile pipeline, not here.",
    )
    identifier: list[FhirIdentifierInput] | None = Field(
        None, description="Identifier for this record. Searched by `identifier`."
    )
    status: StatusCode | None = Field(
        None,
        description="draft | proposed | active | rejected | inactive | entered-in-error (required by R4). Searched by `status`.",
    )
    scope: FhirCodeableConceptInput | None = Field(
        None,
        description="Which of the four areas this resource covers (required by R4). Searched by `scope`.",
    )
    category: list[FhirCodeableConceptInput] | None = Field(
        None,
        description="Classification of the consent statement - for indexing/retrieval (1..* in R4). Searched by `category`.",
    )
    patient: FhirReferenceInput | None = Field(
        None,
        description="Who the consent applies to - Reference(Patient). A relative reference must exist in the caller's org (422 otherwise). Searched by `patient`.",
    )
    dateTime: str | None = Field(
        None,
        description="When this Consent was created or indexed (a FHIR dateTime). Searched by `date`.",
    )
    performer: list[FhirReferenceInput] | None = Field(
        None,
        description="Who is agreeing to the policy and rules - Reference(Organization | Patient | Practitioner | RelatedPerson | PractitionerRole). Searched by `consentor`.",
    )
    organization: list[FhirReferenceInput] | None = Field(
        None,
        description="Custodian of the consent - Reference(Organization). Searched by `organization`.",
    )
    sourceAttachment: FhirAttachmentInput | None = Field(
        None, description="source[x]: the source of the consent, as an Attachment."
    )
    sourceReference: FhirReferenceInput | None = Field(
        None,
        description="source[x]: Reference(Consent | DocumentReference | Contract | QuestionnaireResponse). Searched by `source-reference`.",
    )
    policy: list[ConsentPolicyInput] | None = Field(
        None, description="Policies covered by this consent."
    )
    policyRule: FhirCodeableConceptInput | None = Field(
        None, description="Regulation that this consents to."
    )
    verification: list[ConsentVerificationInput] | None = Field(
        None, description="Consent Verified by patient or family."
    )
    provision: ConsentProvisionInput | None = Field(
        None, description="Constraints to the base Consent.policyRule."
    )


class ConsentCreateSchema(_ConsentFields):
    """POST body - a FHIR R4 Consent resource."""

    model_config = {"json_schema_extra": {"example": _EXAMPLE}}


class ConsentPatchSchema(_ConsentFields):
    """PATCH body - a partial FHIR R4 Consent (merge-patch semantics on top-level elements). Only
    supplied elements are written; omitted ones are left untouched. A supplied element replaces
    the stored value wholesale - a list (even `[]`) replaces every existing entry, an object such
    as `provision` replaces the whole value, and `null` clears it."""

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "inactive",
                "provision": {"type": "deny", "period": {"start": "2026-06-01"}},
            }
        }
    }
