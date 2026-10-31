"""FHIR R4 conformance for `to_fhir_goal()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.
"""

import datetime as dt

import pytest

from app.fhir.mappers.goal import to_fhir_goal
from app.models.enums import IdentifierUse, OrganizationReferenceType
from app.models.goal import (
    GoalAchievementStatusCoding,
    GoalAddresses,
    GoalCategory,
    GoalCategoryCoding,
    GoalDescriptionCoding,
    GoalExpressedByReferenceType,
    GoalIdentifier,
    GoalIdentifierTypeCoding,
    GoalLifecycleStatus,
    GoalModel,
    GoalNote,
    GoalOutcomeCode,
    GoalOutcomeCodeCoding,
    GoalOutcomeReference,
    GoalOutcomeReferenceType,
    GoalPriorityCoding,
    GoalStartCoding,
    GoalSubjectReferenceType,
    GoalTarget,
    GoalTargetDetailCoding,
    GoalTargetMeasureCoding,
)

from .support import assert_valid

goal_pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.goal_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.date(2026, 1, 1)
T = dt.datetime(2026, 1, 1, 12, 0, 0, tzinfo=dt.timezone.utc)

_CHILD_ATTRS = (
    "identifiers",
    "achievement_status_codings",
    "priority_codings",
    "description_codings",
    "start_codings",
    "categories",
    "targets",
    "addresses_list",
    "notes",
    "outcome_codes",
    "outcome_references",
)


def _goal(**overrides) -> GoalModel:
    fields = {
        "id": 1,
        "goal_id": 460001,
        "tenant_id": "org-test",
        "lifecycle_status": GoalLifecycleStatus.active,
        "achievement_status_text": "In Progress",
        "priority_text": "High Priority",
        "description_text": "Follow-up dietary regime",
        "subject_reference": "Patient/10001",
        "subject_type": GoalSubjectReferenceType.Patient,
        "subject_id": 10001,
        "subject_display": "Jane Doe",
        "start_date": D,
        "status_date": D,
        "status_reason": "Adhering to dietary regime",
        "expressed_by_reference": "Practitioner/30001",
        "expressed_by_type": GoalExpressedByReferenceType.Practitioner,
        "expressed_by_id": 30001,
        "expressed_by_display": "Dr. Smith",
        "created_at": T,
        "updated_at": T,
        "created_by": "user-1",
        "updated_by": "user-1",
    }
    fields.update(overrides)
    m = GoalModel()
    for k, v in fields.items():
        setattr(m, k, v)
    for attr in _CHILD_ATTRS:
        if not hasattr(m, attr) or getattr(m, attr) is None:
            setattr(m, attr, [])
    return m


def test_goal_minimal_conformance():
    """Minimal Goal conforming to FHIR R4."""
    model = _goal()
    fhir_dict = to_fhir_goal(model)
    assert fhir_dict["resourceType"] == "Goal"
    assert fhir_dict["id"] == "460001"
    assert fhir_dict["lifecycleStatus"] == "active"
    assert_valid(goal_pb2.Goal, fhir_dict)


def test_goal_full_conformance():
    """Full Goal with all sub-elements populated conforming to FHIR R4."""
    model = _goal()

    ident = GoalIdentifier(
        id=1,
        goal_pk=1,
        tenant_id="org-test",
        use=IdentifierUse.official,
        type_text="Medical Record Number",
        system="http://hospital.example.org",
        value="GOAL-123",
        period_start=T,
        period_end=T + dt.timedelta(days=365),
        assigner_reference="Organization/190001",
        assigner_type=OrganizationReferenceType.Organization,
        assigner_id=190001,
        assigner_display="Example Hospital",
    )
    ident.codings = [
        GoalIdentifierTypeCoding(
            id=1,
            goal_identifier_id=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/v2-0203",
            code="MR",
            display="Medical Record Number",
        )
    ]
    model.identifiers = [ident]

    model.achievement_status_codings = [
        GoalAchievementStatusCoding(
            id=1,
            goal_pk=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/goal-achievement",
            code="in-progress",
            display="In Progress",
        )
    ]

    cat = GoalCategory(
        id=1,
        goal_pk=1,
        tenant_id="org-test",
        text="Dietary",
    )
    cat.codings = [
        GoalCategoryCoding(
            id=1,
            goal_category_id=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/goal-category",
            code="dietary",
            display="Dietary",
        )
    ]
    model.categories = [cat]

    model.priority_codings = [
        GoalPriorityCoding(
            id=1,
            goal_pk=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/goal-priority",
            code="high-priority",
            display="High Priority",
        )
    ]

    model.description_codings = [
        GoalDescriptionCoding(
            id=1,
            goal_pk=1,
            tenant_id="org-test",
            system="http://snomed.info/sct",
            code="281036007",
            display="Follow-up dietary regime",
        )
    ]

    tgt = GoalTarget(
        id=1,
        goal_pk=1,
        tenant_id="org-test",
        measure_text="Weight",
        detail_quantity_value=70,
        detail_quantity_unit="kg",
        detail_quantity_system="http://unitsofmeasure.org",
        detail_quantity_code="kg",
        due_date=D + dt.timedelta(days=180),
    )
    tgt.measure_codings = [
        GoalTargetMeasureCoding(
            id=1,
            goal_target_id=1,
            tenant_id="org-test",
            system="http://loinc.org",
            code="29463-7",
            display="Body weight",
        )
    ]
    tgt.detail_codings = []
    model.targets = [tgt]

    model.addresses_list = [
        GoalAddresses(
            id=1,
            goal_pk=1,
            tenant_id="org-test",
            reference_reference="Condition/120001",
            reference_type="Condition",
            reference_id=120001,
            reference_display="Obesity",
        )
    ]

    model.notes = [
        GoalNote(
            id=1,
            goal_pk=1,
            tenant_id="org-test",
            author_reference="Practitioner/30001",
            author_type=GoalExpressedByReferenceType.Practitioner,
            author_id=30001,
            author_display="Dr. Smith",
            time=T,
            text="Patient motivated to achieve weight goal.",
        )
    ]

    oc = GoalOutcomeCode(
        id=1,
        goal_pk=1,
        tenant_id="org-test",
        text="Normal weight achieved",
    )
    oc.codings = [
        GoalOutcomeCodeCoding(
            id=1,
            goal_outcome_code_id=1,
            tenant_id="org-test",
            system="http://snomed.info/sct",
            code="429074003",
            display="Normal weight",
        )
    ]
    model.outcome_codes = [oc]

    model.outcome_references = [
        GoalOutcomeReference(
            id=1,
            goal_pk=1,
            tenant_id="org-test",
            reference_reference="Observation/160001",
            reference_type=GoalOutcomeReferenceType.Observation,
            reference_id=160001,
            reference_display="Weight measurement",
        )
    ]

    fhir_dict = to_fhir_goal(model)
    assert_valid(goal_pb2.Goal, fhir_dict)
