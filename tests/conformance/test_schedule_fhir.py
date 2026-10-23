"""FHIR R4 conformance for `to_fhir_schedule()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.
"""

import datetime as dt

import pytest

from app.fhir.mappers.schedule import to_fhir_schedule
from app.models.schedule import (
    ScheduleActor,
    ScheduleIdentifier,
    ScheduleIdentifierTypeCoding,
    ScheduleModel,
    ScheduleServiceCategory,
    ScheduleServiceCategoryCoding,
    ScheduleServiceType,
    ScheduleServiceTypeCoding,
    ScheduleSpecialty,
    ScheduleSpecialtyCoding,
)

from .support import assert_valid, fhir_json_text

schedule_pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.schedule_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)

_CHILD_ATTRS = (
    "identifiers", "service_categories", "service_types", "specialties", "actors",
)


def _sch(**overrides) -> ScheduleModel:
    """A Schedule carrying only the columns the model marks NOT NULL, plus
    empty sub-resource lists (nothing is lazy-loadable off a session here).
    `actor` is FHIR R4's one genuinely required (1..*) Schedule field —
    google-fhir-r4 enforces that cardinality strictly, so every case needs
    at least one, same as `_with("actors", ...)` cases provide their own."""
    fields = {
        "schedule_id": 200001,
        "tenant_id": "org-test",
        "active": True,
        "created_by": "u-test",
        "created_at": D,
    }
    fields.update(overrides)
    sch = ScheduleModel(**fields)
    for attr in _CHILD_ATTRS:
        if getattr(sch, attr, None) is None:
            setattr(sch, attr, [])
    sch.actors = [
        ScheduleActor(
            id=1, tenant_id="org-test", reference_type="Practitioner",
            reference_id=30001, created_by="u-test", created_at=D,
        )
    ]
    return sch


def _with(attr, *rows) -> ScheduleModel:
    sch = _sch()
    setattr(sch, attr, list(rows))
    return sch


def _identifier(**kw) -> ScheduleIdentifier:
    i = ScheduleIdentifier(
        **{
            "id": 1, "tenant_id": "org-test", "system": "http://ex.org/ids",
            "value": "SCH-1", "created_by": "u-test", "created_at": D, **kw,
        }
    )
    if i.type_codings is None:
        i.type_codings = []
    return i


# Each CodeableConcept-list field (serviceCategory/serviceType/specialty) is
# a real 0..* child table with its own dedicated Coding grandchild table —
# this maps a parent model class to its matching Coding class so one
# `_cc()` helper covers all three.
_CODING_CLASS = {
    ScheduleServiceCategory: ScheduleServiceCategoryCoding,
    ScheduleServiceType: ScheduleServiceTypeCoding,
    ScheduleSpecialty: ScheduleSpecialtyCoding,
}


def _cc(model_cls, *, codings=None, **kw):
    coding_cls = _CODING_CLASS[model_cls]
    if codings is None:
        codings = [
            coding_cls(
                id=1,
                system="http://terminology.hl7.org/CodeSystem/service-category",
                code="17", display="General Practice",
                created_by="u-test", created_at=D,
            )
        ]
    return model_cls(
        **{
            "id": 1, "tenant_id": "org-test", "codings": codings,
            "created_by": "u-test", "created_at": D, **kw,
        }
    )


# Each case is one distinct shape the mapper can emit. Anything with a
# conditional branch in app/fhir/mappers/schedule/fhir.py should appear here.
CASES = {
    "minimal": _sch(),

    "active_true": _sch(active=True),
    "active_false": _sch(active=False),

    "planning_horizon": _sch(
        planning_horizon_start=D, planning_horizon_end=D
    ),

    "comment": _sch(comment="Walk-in and appointment-based bookings."),

    "identifier_with_type_and_period": _with(
        "identifiers",
        _identifier(
            use="official",
            type_codings=[
                ScheduleIdentifierTypeCoding(
                    id=1,
                    system="http://terminology.hl7.org/CodeSystem/v2-0203",
                    version="2.9", code="PRN", display="Provider number",
                    user_selected=True, created_by="u-test", created_at=D,
                )
            ],
            type_text="Provider number",
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

    "service_category_with_text": _with(
        "service_categories", _cc(ScheduleServiceCategory, text="General Practice")
    ),
    "service_type_with_text": _with(
        "service_types",
        _cc(
            ScheduleServiceType,
            codings=[
                ScheduleServiceTypeCoding(
                    id=1, system="http://example.org/service-type", code="57",
                    display="Immunization", created_by="u-test", created_at=D,
                )
            ],
            text="Immunization",
        ),
    ),
    "specialty_with_text": _with(
        "specialties",
        _cc(
            ScheduleSpecialty,
            codings=[
                ScheduleSpecialtyCoding(
                    id=1, system="http://snomed.info/sct", code="408443003",
                    display="General medical practice",
                    created_by="u-test", created_at=D,
                )
            ],
            text="General medical practice",
        ),
    ),

    "actor_practitioner_resolved": _with(
        "actors",
        ScheduleActor(
            id=1, tenant_id="org-test", reference_type="Practitioner",
            reference_id=30001, reference_display="Dr. Jane Smith",
            created_by="u-test", created_at=D,
        ),
    ),
    "actor_practitioner_role_resolved": _with(
        "actors",
        ScheduleActor(
            id=1, tenant_id="org-test", reference_type="PractitionerRole",
            reference_id=140001, reference_display="GP role",
            created_by="u-test", created_at=D,
        ),
    ),
    "actor_healthcare_service_resolved": _with(
        "actors",
        ScheduleActor(
            id=1, tenant_id="org-test", reference_type="HealthcareService",
            reference_id=150001, reference_display="Physio",
            created_by="u-test", created_at=D,
        ),
    ),
    "actor_location_resolved": _with(
        "actors",
        ScheduleActor(
            id=1, tenant_id="org-test", reference_type="Location",
            reference_id=230001, reference_display="Main Building",
            created_by="u-test", created_at=D,
        ),
    ),
    "actor_identifier_fallback": _with(
        "actors",
        ScheduleActor(
            id=1, tenant_id="org-test", reference_identifier_system="urn:patient-registry",
            reference_identifier_value="PAT-1", reference_display="Jane Patient",
            created_by="u-test", created_at=D,
        ),
    ),
    "actor_multiple": _with(
        "actors",
        ScheduleActor(
            id=1, tenant_id="org-test", reference_type="Practitioner",
            reference_id=30001, created_by="u-test", created_at=D,
        ),
        ScheduleActor(
            id=2, tenant_id="org-test", reference_type="Location",
            reference_id=230001, created_by="u-test", created_at=D,
        ),
    ),
}


@pytest.mark.parametrize("case", sorted(CASES), ids=sorted(CASES))
def test_schedule_mapper_emits_valid_fhir_r4(case):
    assert_valid(schedule_pb2.Schedule, to_fhir_schedule(CASES[case]))


# ── Guarding the oracle ────────────────────────────────────────────────────────
# If google-fhir-r4 ever stops validating — a version bump, a changed API, a
# silently-swallowed error — every test above would keep passing while checking
# nothing. These deliberately-broken payloads prove the check still has teeth.

@pytest.mark.parametrize(
    "label,broken",
    [
        ("serviceCategory as strings not CodeableConcepts", {"serviceCategory": ["gp"]}),
        ("misspelled element", {"actor2": [{"reference": "Practitioner/1"}]}),
        ("active as string not boolean", {"active": "yes"}),
        ("identifier as string not object", {"identifier": ["SCH-1"]}),
        ("actor as string not Reference", {"actor": ["Practitioner/1"]}),
        ("planningHorizon.start not a date", {"planningHorizon": {"start": "not-a-date"}}),
        ("specialty as strings not CodeableConcepts", {"specialty": ["gp"]}),
    ],
)
def test_validator_rejects_invalid_fhir(label, broken):
    from google.fhir.r4 import json_format

    payload = {
        "resourceType": "Schedule", "id": "200001",
        "actor": [{"reference": "Practitioner/30001"}], **broken,
    }
    with pytest.raises(Exception):  # noqa: B017 — the library raises several types
        json_format.json_fhir_string_to_proto(
            fhir_json_text(payload), schedule_pb2.Schedule, validate=True
        )
