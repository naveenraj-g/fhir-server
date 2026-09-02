"""FHIR R4 conformance for `to_fhir_practitioner_role()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.
"""

import datetime as dt

import pytest

from app.fhir.mappers.practitioner_role import to_fhir_practitioner_role
from app.models.practitioner_role import (
    PractitionerRoleAvailableTime,
    PractitionerRoleCode,
    PractitionerRoleEndpoint,
    PractitionerRoleHealthcareService,
    PractitionerRoleIdentifier,
    PractitionerRoleLocation,
    PractitionerRoleModel,
    PractitionerRoleNotAvailable,
    PractitionerRoleSpecialty,
    PractitionerRoleTelecom,
)

from .support import assert_valid, fhir_json_text

practitioner_role_pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.practitioner_role_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)

_CHILD_ATTRS = (
    "identifiers", "codes", "specialties", "locations", "healthcare_services",
    "telecoms", "available_times", "not_available", "endpoints",
)


def _pr(**overrides) -> PractitionerRoleModel:
    """A PractitionerRole carrying only the columns the model marks NOT
    NULL, plus empty sub-resource lists (nothing is lazy-loadable off a
    session here)."""
    fields = {
        "practitioner_role_id": 140001,
        "org_id": "org-test",
        "active": True,
        "created_by": "u-test",
        "created_at": D,
    }
    fields.update(overrides)
    pr = PractitionerRoleModel(**fields)
    for attr in _CHILD_ATTRS:
        if getattr(pr, attr, None) is None:
            setattr(pr, attr, [])
    return pr


def _with(attr, *rows) -> PractitionerRoleModel:
    pr = _pr()
    setattr(pr, attr, list(rows))
    return pr


def _identifier(**kw) -> PractitionerRoleIdentifier:
    return PractitionerRoleIdentifier(
        **{
            "id": 1, "org_id": "org-test", "system": "http://ex.org/ids",
            "value": "PR-1", "created_by": "u-test", "created_at": D, **kw,
        }
    )


def _cc(model_cls, **kw):
    return model_cls(
        **{
            "id": 1, "org_id": "org-test",
            "coding_system": "http://snomed.info/sct",
            "coding_code": "59058001", "coding_display": "General physician",
            "created_by": "u-test", "created_at": D, **kw,
        }
    )


# Each case is one distinct shape the mapper can emit. Anything with a
# conditional branch in app/fhir/mappers/practitioner_role/fhir.py should
# appear here.
CASES = {
    "minimal": _pr(),

    "active_false": _pr(active=False),

    "period_full": _pr(period_start=D, period_end=D),
    "period_start_only": _pr(period_start=D),

    "practitioner_resolved": _pr(
        practitioner_type="Practitioner", practitioner_id=30001,
        practitioner_display="Dr. Jane Smith",
    ),
    "practitioner_identifier_fallback": _pr(
        practitioner_identifier_system="urn:practitioner-registry",
        practitioner_identifier_value="PRAC-9",
        practitioner_identifier_use="official",
    ),

    "organization_resolved": _pr(
        organization_type="Organization", organization_id=190001,
        organization_display="General Hospital",
    ),
    "organization_identifier_fallback": _pr(
        organization_identifier_system="urn:org-registry",
        organization_identifier_value="ORG-9",
    ),

    "availability_exceptions": _pr(
        availability_exceptions="Not available on public holidays."
    ),

    "identifier_with_type_and_period": _with(
        "identifiers",
        _identifier(
            use="official",
            type_system="http://terminology.hl7.org/CodeSystem/v2-0203",
            type_version="2.9",
            type_code="PRN",
            type_display="Provider number",
            type_text="Provider number",
            type_user_selected=True,
            period_start=D,
            period_end=D,
        ),
    ),
    "identifier_assigner_resolved": _with(
        "identifiers",
        _identifier(
            assigner_type="Organization", assigner_id=190001, assigner_display="Acme"
        ),
    ),
    "identifier_assigner_fallback": _with(
        "identifiers",
        _identifier(
            assigner_identifier_system="urn:external-registry",
            assigner_identifier_value="EXTERNAL-1",
            assigner_identifier_use="official",
        ),
    ),

    "code_with_text": _with(
        "codes",
        _cc(
            PractitionerRoleCode,
            coding_code="59058001", coding_display="General physician",
            text="General physician", coding_user_selected=True,
        ),
    ),
    "specialty_with_text": _with(
        "specialties",
        _cc(
            PractitionerRoleSpecialty,
            coding_system="http://snomed.info/sct",
            coding_code="394814009", coding_display="General practice",
            text="General practice",
        ),
    ),

    "location_resolved": _with(
        "locations",
        PractitionerRoleLocation(
            id=1, org_id="org-test", reference_type="Location", reference_id=230001,
            reference_display="Main Building", created_by="u-test", created_at=D,
        ),
    ),
    "location_identifier_fallback": _with(
        "locations",
        PractitionerRoleLocation(
            id=1, org_id="org-test", reference_identifier_system="urn:loc-registry",
            reference_identifier_value="LOC-9", created_by="u-test", created_at=D,
        ),
    ),

    "healthcare_service_resolved": _with(
        "healthcare_services",
        PractitionerRoleHealthcareService(
            id=1, org_id="org-test", reference_type="HealthcareService",
            reference_id=150001, reference_display="Cardiology Services",
            created_by="u-test", created_at=D,
        ),
    ),
    "healthcare_service_identifier_fallback": _with(
        "healthcare_services",
        PractitionerRoleHealthcareService(
            id=1, org_id="org-test", reference_identifier_system="urn:hs-registry",
            reference_identifier_value="HS-9", created_by="u-test", created_at=D,
        ),
    ),

    "telecoms_with_rank_and_period": _with(
        "telecoms",
        PractitionerRoleTelecom(
            id=1, org_id="org-test", system="phone", value="555-1234", use="work",
            rank=1, period_start=D, period_end=D, created_by="u-test", created_at=D,
        ),
        PractitionerRoleTelecom(
            id=2, org_id="org-test", system="email", value="a@b.example",
            created_by="u-test", created_at=D,
        ),
    ),

    "available_time_all_day_no_times": _with(
        "available_times",
        PractitionerRoleAvailableTime(
            id=1, org_id="org-test", days_of_week="sat,sun", all_day=True,
            created_by="u-test", created_at=D,
        ),
    ),
    "available_time_all_seven_days_edge_times": _with(
        "available_times",
        PractitionerRoleAvailableTime(
            id=1, org_id="org-test", days_of_week="mon,tue,wed,thu,fri,sat,sun",
            all_day=False, available_start_time=dt.time(0, 0),
            available_end_time=dt.time(23, 59, 59), created_by="u-test", created_at=D,
        ),
    ),

    "not_available_description_only": _with(
        "not_available",
        PractitionerRoleNotAvailable(
            id=1, org_id="org-test", description="Closed for renovations.",
            created_by="u-test", created_at=D,
        ),
    ),
    "not_available_with_during": _with(
        "not_available",
        PractitionerRoleNotAvailable(
            id=1, org_id="org-test", description="Annual leave.",
            during_start=D, during_end=D, created_by="u-test", created_at=D,
        ),
    ),

    "endpoint_resolved": _with(
        "endpoints",
        PractitionerRoleEndpoint(
            id=1, org_id="org-test", reference_type="Endpoint", reference_id=7,
            reference_display="Main endpoint", created_by="u-test", created_at=D,
        ),
    ),
    "endpoint_identifier_fallback": _with(
        "endpoints",
        PractitionerRoleEndpoint(
            id=1, org_id="org-test", reference_identifier_system="urn:ext-endpoint",
            reference_identifier_value="EP-1", created_by="u-test", created_at=D,
        ),
    ),
}


@pytest.mark.parametrize("case", sorted(CASES), ids=sorted(CASES))
def test_practitioner_role_mapper_emits_valid_fhir_r4(case):
    assert_valid(
        practitioner_role_pb2.PractitionerRole, to_fhir_practitioner_role(CASES[case])
    )


# ── Guarding the oracle ────────────────────────────────────────────────────────
# If google-fhir-r4 ever stops validating — a version bump, a changed API, a
# silently-swallowed error — every test above would keep passing while checking
# nothing. These deliberately-broken payloads prove the check still has teeth.

@pytest.mark.parametrize(
    "label,broken",
    [
        ("bad daysOfWeek code", {"availableTime": [{"daysOfWeek": ["funday"]}]}),
        ("availableStartTime not a time", {"availableTime": [{"availableStartTime": "9am"}]}),
        ("code as strings not CodeableConcepts", {"code": ["general-practice"]}),
        ("misspelled element", {"practitioner2": {"reference": "Practitioner/1"}}),
        ("notAvailable missing required description", {"notAvailable": [{"during": {"start": "2026-01-01"}}]}),
        ("active as string not boolean", {"active": "yes"}),
        ("identifier as string not object", {"identifier": ["PR-1"]}),
    ],
)
def test_validator_rejects_invalid_fhir(label, broken):
    from google.fhir.r4 import json_format

    payload = {
        "resourceType": "PractitionerRole", "id": "140001", **broken,
    }
    with pytest.raises(Exception):  # noqa: B017 — the library raises several types
        json_format.json_fhir_string_to_proto(
            fhir_json_text(payload), practitioner_role_pb2.PractitionerRole, validate=True
        )
