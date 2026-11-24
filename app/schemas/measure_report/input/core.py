from __future__ import annotations

from typing import Literal

from pydantic import Field

from app.schemas.fhir_input import (
    FhirCodeableConceptInput,
    FhirIdentifierInput,
    FhirInputModel,
    FhirPeriodInput,
    FhirReferenceInput,
)

# MeasureReportStatus and MeasureReportType (the required bindings of MeasureReport.status and
# .type).
StatusCode = Literal["complete", "pending", "error"]
TypeCode = Literal["individual", "subject-list", "summary", "data-collection"]

_EXAMPLE = {
    "resourceType": "MeasureReport",
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/measure-report-id",
            "value": "MR-1001",
        }
    ],
    "status": "complete",
    "type": "summary",
    "measure": "https://fhir-server.dev/fhir/Measure/readmission",
    "subject": {"reference": "Group/430001"},
    "date": "2026-02-01T10:00:00Z",
    "reporter": {"reference": "Organization/190001"},
    "period": {"start": "2026-01-01", "end": "2026-01-31"},
    "improvementNotation": {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/measure-improvement-notation",
                "code": "increase",
            }
        ]
    },
    "group": [
        {
            "code": {"text": "overall"},
            "population": [
                {
                    "code": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/measure-population",
                                "code": "initial-population",
                            }
                        ]
                    },
                    "count": 120,
                },
                {
                    "code": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/measure-population",
                                "code": "numerator",
                            }
                        ]
                    },
                    "count": 18,
                },
            ],
            "measureScore": {"value": 0.15},
        }
    ],
}


class _MeasureReportFields(FhirInputModel):
    """Every writable MeasureReport element, in genuine FHIR R4 shape
    (https://www.hl7.org/fhir/R4/measurereport.html). Create and patch accept exactly the same
    fields. R4 requires `status`, `type`, `measure` and `period`; the native validator checks the
    required complex elements and `measure` / `period`, while only the `java_validator` backend
    rejects a missing primitive `status` / `type`.

    The validated body is stored whole (MeasureReportModel.content), so any valid R4 element is
    kept - including ones this model does not declare. Server-managed elements are ignored if
    sent: `id` (assigned from the measure_report_id sequence) and `meta` (audit/tenant data,
    stamped on at read time). org_id and created_by/updated_by come from the verified JWT
    (actor.org_id / actor.sub), never the body. There is no user_id."""

    resourceType: Literal["MeasureReport"] | None = Field(
        None, description="Optional; if supplied it must be 'MeasureReport'."
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries - validated by the profile pipeline, not here.",
    )
    identifier: list[FhirIdentifierInput] | None = Field(
        None, description="Additional identifier. Searched by `identifier`."
    )
    status: StatusCode | None = Field(
        None,
        description="complete | pending | error (required by R4). Searched by `status`.",
    )
    type: TypeCode | None = Field(
        None,
        description="individual | subject-list | summary | data-collection (required by R4).",
    )
    measure: str | None = Field(
        None,
        description="What measure was calculated - the canonical URL of a Measure (required by R4). Searched by `measure`; a relative `Measure/<id>` form is resolved against the stored Measure.",
    )
    subject: FhirReferenceInput | None = Field(
        None,
        description="What individual(s) the report is for - Reference(Patient | Practitioner | PractitionerRole | Location | Device | RelatedPerson | Group). Searched by `subject` / `patient`.",
    )
    date: str | None = Field(
        None,
        description="When the report was generated (a FHIR dateTime). Searched by `date`.",
    )
    reporter: FhirReferenceInput | None = Field(
        None,
        description="Who is reporting the data - Reference(Practitioner | PractitionerRole | Location | Organization). Searched by `reporter`.",
    )
    period: FhirPeriodInput | None = Field(
        None,
        description="What period the report covers (required by R4). Searched by `period`.",
    )
    improvementNotation: FhirCodeableConceptInput | None = Field(
        None, description="increase | decrease."
    )
    group: list[dict] | None = Field(
        None,
        description="Measure results for each group: [{code, population[{code, count, subjectResults}], measureScore, stratifier[{code[], stratum[{value, component[], population[], measureScore}]}]}].",
    )
    evaluatedResource: list[FhirReferenceInput] | None = Field(
        None,
        description="What data was used to calculate the measure score - Reference(Any). A relative reference to a rebuilt resource must exist in the caller's org (422 otherwise). Searched by `evaluated-resource`.",
    )


class MeasureReportCreateSchema(_MeasureReportFields):
    """POST body - a FHIR R4 MeasureReport resource."""

    model_config = {"json_schema_extra": {"example": _EXAMPLE}}


class MeasureReportPatchSchema(_MeasureReportFields):
    """PATCH body - a partial FHIR R4 MeasureReport (merge-patch semantics on top-level
    elements). Only supplied elements are written; omitted ones are left untouched. A supplied
    element replaces the stored value wholesale - a list (even `[]`) replaces every existing
    entry, an object replaces the whole value, and `null` clears it."""

    model_config = {
        "json_schema_extra": {
            "example": {"status": "complete", "date": "2026-02-02T10:00:00Z"},
        }
    }
