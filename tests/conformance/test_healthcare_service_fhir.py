"""FHIR R4 conformance for `to_fhir_healthcare_service()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.
"""

import datetime as dt

import pytest

from app.fhir.mappers.healthcare_service import to_fhir_healthcare_service
from app.models.healthcare_service import (
    HealthcareServiceAvailableTime,
    HealthcareServiceCategory,
    HealthcareServiceCharacteristic,
    HealthcareServiceCommunication,
    HealthcareServiceCoverageArea,
    HealthcareServiceEligibility,
    HealthcareServiceEndpoint,
    HealthcareServiceIdentifier,
    HealthcareServiceLocation,
    HealthcareServiceModel,
    HealthcareServiceNotAvailable,
    HealthcareServiceProgram,
    HealthcareServiceReferralMethod,
    HealthcareServiceServiceProvisionCode,
    HealthcareServiceSpecialty,
    HealthcareServiceTelecom,
    HealthcareServiceType,
)

from .support import assert_valid, fhir_json_text

healthcare_service_pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.healthcare_service_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)

_CHILD_ATTRS = (
    "identifiers", "categories", "types", "specialties", "locations",
    "telecoms", "coverage_areas", "service_provision_codes", "eligibilities",
    "programs", "characteristics", "communications", "referral_methods",
    "available_times", "not_available", "endpoints",
)


def _hs(**overrides) -> HealthcareServiceModel:
    """A HealthcareService carrying only the columns the model marks NOT
    NULL, plus empty sub-resource lists (nothing is lazy-loadable off a
    session here)."""
    fields = {
        "healthcare_service_id": 150001,
        "org_id": "org-test",
        "name": "South Wing Physio",
        "created_by": "u-test",
        "created_at": D,
    }
    fields.update(overrides)
    hs = HealthcareServiceModel(**fields)
    for attr in _CHILD_ATTRS:
        if getattr(hs, attr, None) is None:
            setattr(hs, attr, [])
    return hs


def _with(attr, *rows) -> HealthcareServiceModel:
    hs = _hs()
    setattr(hs, attr, list(rows))
    return hs


def _identifier(**kw) -> HealthcareServiceIdentifier:
    return HealthcareServiceIdentifier(
        **{
            "id": 1, "org_id": "org-test", "system": "http://ex.org/ids",
            "value": "HS-1", "created_by": "u-test", "created_at": D, **kw,
        }
    )


def _cc(model_cls, **kw):
    return model_cls(
        **{
            "id": 1, "org_id": "org-test",
            "coding_system": "http://terminology.hl7.org/CodeSystem/service-category",
            "coding_code": "8", "coding_display": "Counselling",
            "created_by": "u-test", "created_at": D, **kw,
        }
    )


# Each case is one distinct shape the mapper can emit. Anything with a
# conditional branch in app/fhir/mappers/healthcare_service/fhir.py should
# appear here.
CASES = {
    "minimal": _hs(),

    "active_true": _hs(active=True),
    "active_false": _hs(active=False),

    "provided_by_resolved": _hs(
        provided_by_type="Organization", provided_by_id=190001,
        provided_by_display="General Hospital",
    ),
    "provided_by_identifier_fallback": _hs(
        provided_by_identifier_system="urn:org-registry",
        provided_by_identifier_value="ORG-9",
        provided_by_identifier_use="official",
    ),

    "comment": _hs(comment="Referral required for new patients."),
    "extra_details": _hs(extra_details="# Markdown details\n\nMore info here."),

    "photo_full": _hs(
        photo_content_type="image/png",
        photo_language="en",
        photo_data="YWJjMTIz",
        photo_url="https://example.org/photo.png",
        photo_size=1024,
        photo_hash="ZGVhZGJlZWY=",
        photo_title="Clinic photo",
        photo_creation=D,
    ),

    "appointment_required_true": _hs(appointment_required=True),
    "appointment_required_false": _hs(appointment_required=False),
    "availability_exceptions": _hs(
        availability_exceptions="Closed on public holidays."
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

    "category_with_text": _with(
        "categories", _cc(HealthcareServiceCategory, text="Counselling")
    ),
    "type_with_text": _with(
        "types",
        _cc(
            HealthcareServiceType,
            coding_system="http://snomed.info/sct",
            coding_code="394814009",
            coding_display="General practice",
            text="General practice",
            coding_user_selected=True,
        ),
    ),
    "specialty_with_text": _with(
        "specialties",
        _cc(
            HealthcareServiceSpecialty,
            coding_system="http://snomed.info/sct",
            coding_code="408443003",
            coding_display="General medical practice",
            text="General medical practice",
        ),
    ),

    "location_resolved": _with(
        "locations",
        HealthcareServiceLocation(
            id=1, org_id="org-test", reference_type="Location", reference_id=230001,
            reference_display="Main Building", created_by="u-test", created_at=D,
        ),
    ),
    "location_identifier_fallback": _with(
        "locations",
        HealthcareServiceLocation(
            id=1, org_id="org-test", reference_identifier_system="urn:loc-registry",
            reference_identifier_value="LOC-9", created_by="u-test", created_at=D,
        ),
    ),

    "telecoms_with_rank_and_period": _with(
        "telecoms",
        HealthcareServiceTelecom(
            id=1, org_id="org-test", system="phone", value="2328", use="work",
            rank=1, period_start=D, period_end=D, created_by="u-test", created_at=D,
        ),
        HealthcareServiceTelecom(
            id=2, org_id="org-test", system="email", value="a@b.example",
            created_by="u-test", created_at=D,
        ),
    ),

    "coverage_area_resolved": _with(
        "coverage_areas",
        HealthcareServiceCoverageArea(
            id=1, org_id="org-test", reference_type="Location", reference_id=230001,
            reference_display="Downtown catchment", created_by="u-test", created_at=D,
        ),
    ),
    "coverage_area_identifier_fallback": _with(
        "coverage_areas",
        HealthcareServiceCoverageArea(
            id=1, org_id="org-test", reference_identifier_system="urn:loc-registry",
            reference_identifier_value="LOC-8", created_by="u-test", created_at=D,
        ),
    ),

    "service_provision_code_with_text": _with(
        "service_provision_codes",
        _cc(
            HealthcareServiceServiceProvisionCode,
            coding_system="http://terminology.hl7.org/CodeSystem/service-provision-conditions",
            coding_code="free", coding_display="Free", text="Free",
        ),
    ),

    "eligibility_code_and_comment": _with(
        "eligibilities",
        HealthcareServiceEligibility(
            id=1, org_id="org-test",
            code_system="http://terminology.hl7.org/CodeSystem/eligibility",
            code_code="ind", code_display="Indigenous population",
            code_text="Indigenous population",
            comment="Must provide proof of eligibility.",
            created_by="u-test", created_at=D,
        ),
    ),
    "eligibility_comment_only": _with(
        "eligibilities",
        HealthcareServiceEligibility(
            id=1, org_id="org-test", comment="Referral required.",
            created_by="u-test", created_at=D,
        ),
    ),

    "program_with_text": _with(
        "programs",
        _cc(
            HealthcareServiceProgram,
            coding_system="http://example.org/programs",
            coding_code="mh", coding_display="Mental Health", text="Mental Health",
        ),
    ),
    "characteristic_with_text": _with(
        "characteristics",
        _cc(
            HealthcareServiceCharacteristic,
            coding_system="http://example.org/characteristics",
            coding_code="wheelchair", coding_display="Wheelchair accessible",
            text="Wheelchair accessible",
        ),
    ),
    "communication_with_text": _with(
        "communications",
        _cc(
            HealthcareServiceCommunication,
            coding_system="urn:ietf:bcp:47",
            coding_code="en", coding_display="English", text="English",
        ),
    ),
    "referral_method_with_text": _with(
        "referral_methods",
        _cc(
            HealthcareServiceReferralMethod,
            coding_system="http://example.org/referral-method",
            coding_code="phone", coding_display="Phone", text="Phone",
        ),
    ),

    "available_time_all_day_no_times": _with(
        "available_times",
        HealthcareServiceAvailableTime(
            id=1, org_id="org-test", days_of_week="sat,sun", all_day=True,
            created_by="u-test", created_at=D,
        ),
    ),
    "available_time_all_seven_days_edge_times": _with(
        "available_times",
        HealthcareServiceAvailableTime(
            id=1, org_id="org-test", days_of_week="mon,tue,wed,thu,fri,sat,sun",
            all_day=False, available_start_time=dt.time(0, 0),
            available_end_time=dt.time(23, 59, 59), created_by="u-test", created_at=D,
        ),
    ),

    "not_available_description_only": _with(
        "not_available",
        HealthcareServiceNotAvailable(
            id=1, org_id="org-test", description="Closed for renovations.",
            created_by="u-test", created_at=D,
        ),
    ),
    "not_available_with_during": _with(
        "not_available",
        HealthcareServiceNotAvailable(
            id=1, org_id="org-test", description="Annual maintenance.",
            during_start=D, during_end=D, created_by="u-test", created_at=D,
        ),
    ),

    "endpoint_resolved": _with(
        "endpoints",
        HealthcareServiceEndpoint(
            id=1, org_id="org-test", reference_type="Endpoint", reference_id=7,
            reference_display="Main endpoint", created_by="u-test", created_at=D,
        ),
    ),
    "endpoint_identifier_fallback": _with(
        "endpoints",
        HealthcareServiceEndpoint(
            id=1, org_id="org-test", reference_identifier_system="urn:ext-endpoint",
            reference_identifier_value="EP-1", created_by="u-test", created_at=D,
        ),
    ),
}


@pytest.mark.parametrize("case", sorted(CASES), ids=sorted(CASES))
def test_healthcare_service_mapper_emits_valid_fhir_r4(case):
    assert_valid(
        healthcare_service_pb2.HealthcareService, to_fhir_healthcare_service(CASES[case])
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
        ("category as strings not CodeableConcepts", {"category": ["counselling"]}),
        ("misspelled element", {"providedBy2": {"reference": "Organization/1"}}),
        ("notAvailable missing required description", {"notAvailable": [{"during": {"start": "2026-01-01"}}]}),
        ("active as string not boolean", {"active": "yes"}),
        ("identifier as string not object", {"identifier": ["HS-1"]}),
    ],
)
def test_validator_rejects_invalid_fhir(label, broken):
    from google.fhir.r4 import json_format

    payload = {
        "resourceType": "HealthcareService", "id": "150001",
        "name": "South Wing Physio", **broken,
    }
    with pytest.raises(Exception):  # noqa: B017 — the library raises several types
        json_format.json_fhir_string_to_proto(
            fhir_json_text(payload), healthcare_service_pb2.HealthcareService, validate=True
        )
