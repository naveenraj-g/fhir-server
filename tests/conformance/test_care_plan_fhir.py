"""FHIR R4 conformance for `to_fhir_care_plan()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.
"""

import datetime as dt

import pytest

from app.fhir.mappers.care_plan import to_fhir_care_plan
from app.models.care_plan import (
    CarePlanActivity,
    CarePlanActivityDetailCodeCoding,
    CarePlanActivityDetailGoal,
    CarePlanActivityDetailPerformer,
    CarePlanActivityDetailPerformerReferenceType,
    CarePlanActivityDetailProductCoding,
    CarePlanActivityDetailReasonCode,
    CarePlanActivityDetailReasonCodeCoding,
    CarePlanActivityDetailReasonReference,
    CarePlanActivityDetailReasonReferenceType,
    CarePlanActivityDetailStatusReasonCoding,
    CarePlanActivityKind,
    CarePlanActivityOutcomeCC,
    CarePlanActivityOutcomeCCCoding,
    CarePlanActivityOutcomeReference,
    CarePlanActivityProgress,
    CarePlanActivityReferenceType,
    CarePlanActivityStatus,
    CarePlanAddresses,
    CarePlanAddressesReferenceType,
    CarePlanAuthorReferenceType,
    CarePlanBasedOn,
    CarePlanBasedOnReferenceType,
    CarePlanCareTeam,
    CarePlanCareTeamReferenceType,
    CarePlanCategory,
    CarePlanCategoryCoding,
    CarePlanContributor,
    CarePlanContributorReferenceType,
    CarePlanEncounterReferenceType,
    CarePlanGoal,
    CarePlanGoalReferenceType,
    CarePlanIdentifier,
    CarePlanIdentifierTypeCoding,
    CarePlanIntent,
    CarePlanLocationReferenceType,
    CarePlanModel,
    CarePlanNote,
    CarePlanPartOf,
    CarePlanPartOfReferenceType,
    CarePlanProductReferenceType,
    CarePlanQuantityComparator,
    CarePlanReplaces,
    CarePlanReplacesReferenceType,
    CarePlanStatus,
    CarePlanSubjectReferenceType,
)
from app.models.enums import (
    IdentifierUse,
    OrganizationReferenceType,
)

from .support import assert_valid

care_plan_pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.care_plan_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, 12, 0, 0, tzinfo=dt.timezone.utc)

_CHILD_ATTRS = (
    "identifiers",
    "categories",
    "based_on",
    "replaces",
    "part_of",
    "contributors",
    "care_teams",
    "addresses",
    "goals",
    "activities",
    "notes",
)


def _care_plan(**overrides) -> CarePlanModel:
    fields = {
        "id": 1,
        "care_plan_id": 290001,
        "tenant_id": "org-test",
        "status": CarePlanStatus.active,
        "intent": CarePlanIntent.plan,
        "subject_reference": "Patient/10001",
        "subject_type": CarePlanSubjectReferenceType.Patient,
        "subject_id": 10001,
        "subject_display": "Test Patient",
        "created_by": "u-test",
        "created_at": D,
        "updated_at": D,
        "extension": [],
    }
    fields.update(overrides)
    cp = CarePlanModel(**fields)
    for attr in _CHILD_ATTRS:
        if getattr(cp, attr, None) is None:
            setattr(cp, attr, [])
    return cp


def test_minimal_care_plan_conforms():
    cp = _care_plan()
    out = to_fhir_care_plan(cp)
    assert out["resourceType"] == "CarePlan"
    assert out["id"] == "290001"
    assert out["status"] == "active"
    assert out["intent"] == "plan"
    assert out["subject"]["reference"] == "Patient/10001"
    assert_valid(care_plan_pb2.CarePlan, out)


def test_care_plan_identifiers_conforms():
    ident = CarePlanIdentifier(
        id=1,
        care_plan_pk=1,
        tenant_id="org-test",
        use=IdentifierUse.official,
        type_text="Plan ID",
        system="http://example.org/plans",
        value="PLAN-999",
        period_start=D,
        period_end=D,
        assigner_reference="Organization/190001",
        assigner_type=OrganizationReferenceType.Organization,
        assigner_id=190001,
        assigner_display="Acme Hospital",
        created_by="u-test",
    )
    ident.type_codings = [
        CarePlanIdentifierTypeCoding(
            id=1,
            identifier_id=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/v2-0203",
            code="PLAC",
            display="Placer Identifier",
            created_by="u-test",
        )
    ]
    cp = _care_plan(identifiers=[ident])
    out = to_fhir_care_plan(cp)
    assert len(out["identifier"]) == 1
    assert out["identifier"][0]["value"] == "PLAN-999"
    assert out["identifier"][0]["use"] == "official"
    assert out["identifier"][0]["assigner"]["reference"] == "Organization/190001"
    assert_valid(care_plan_pb2.CarePlan, out)


def test_care_plan_categories_conforms():
    cat = CarePlanCategory(
        id=1,
        care_plan_pk=1,
        tenant_id="org-test",
        text="Weight management",
        created_by="u-test",
    )
    cat.codings = [
        CarePlanCategoryCoding(
            id=1,
            category_id=1,
            tenant_id="org-test",
            system="http://snomed.info/sct",
            code="408545009",
            display="Weight management plan",
            created_by="u-test",
        )
    ]
    cp = _care_plan(categories=[cat])
    out = to_fhir_care_plan(cp)
    assert len(out["category"]) == 1
    assert out["category"][0]["text"] == "Weight management"
    assert out["category"][0]["coding"][0]["code"] == "408545009"
    assert_valid(care_plan_pb2.CarePlan, out)


def test_care_plan_instantiates_conforms():
    cp = _care_plan(
        instantiates_canonical=["http://example.org/protocols/diabetes"],
        instantiates_uri=["http://example.org/guidelines/gl-123"],
    )
    out = to_fhir_care_plan(cp)
    assert out["instantiatesCanonical"] == ["http://example.org/protocols/diabetes"]
    assert out["instantiatesUri"] == ["http://example.org/guidelines/gl-123"]
    assert_valid(care_plan_pb2.CarePlan, out)


def test_care_plan_lifecycle_references_conforms():
    bo = CarePlanBasedOn(
        id=1,
        care_plan_pk=1,
        tenant_id="org-test",
        reference_reference="CarePlan/290002",
        reference_type=CarePlanBasedOnReferenceType.CarePlan,
        reference_id=290002,
        created_by="u-test",
    )
    rep = CarePlanReplaces(
        id=1,
        care_plan_pk=1,
        tenant_id="org-test",
        reference_reference="CarePlan/290000",
        reference_type=CarePlanReplacesReferenceType.CarePlan,
        reference_id=290000,
        created_by="u-test",
    )
    po = CarePlanPartOf(
        id=1,
        care_plan_pk=1,
        tenant_id="org-test",
        reference_reference="CarePlan/290010",
        reference_type=CarePlanPartOfReferenceType.CarePlan,
        reference_id=290010,
        created_by="u-test",
    )
    cp = _care_plan(based_on=[bo], replaces=[rep], part_of=[po])
    out = to_fhir_care_plan(cp)
    assert out["basedOn"][0]["reference"] == "CarePlan/290002"
    assert out["replaces"][0]["reference"] == "CarePlan/290000"
    assert out["partOf"][0]["reference"] == "CarePlan/290010"
    assert_valid(care_plan_pb2.CarePlan, out)


def test_care_plan_actors_conforms():
    contrib = CarePlanContributor(
        id=1,
        care_plan_pk=1,
        tenant_id="org-test",
        reference_reference="Practitioner/30002",
        reference_type=CarePlanContributorReferenceType.Practitioner,
        reference_id=30002,
        reference_display="Dr. Smith",
        created_by="u-test",
    )
    ct = CarePlanCareTeam(
        id=1,
        care_plan_pk=1,
        tenant_id="org-test",
        reference_reference="CareTeam/1",
        reference_type=CarePlanCareTeamReferenceType.CareTeam,
        reference_id=1,
        created_by="u-test",
    )
    cp = _care_plan(
        author_reference="Practitioner/30001",
        author_type=CarePlanAuthorReferenceType.Practitioner,
        author_id=30001,
        author_display="Dr. Lead",
        contributors=[contrib],
        care_teams=[ct],
    )
    out = to_fhir_care_plan(cp)
    assert out["author"]["reference"] == "Practitioner/30001"
    assert out["contributor"][0]["reference"] == "Practitioner/30002"
    assert out["careTeam"][0]["reference"] == "CareTeam/1"
    assert_valid(care_plan_pb2.CarePlan, out)


def test_care_plan_clinical_context_conforms():
    addr = CarePlanAddresses(
        id=1,
        care_plan_pk=1,
        tenant_id="org-test",
        reference_reference="Condition/120001",
        reference_type=CarePlanAddressesReferenceType.Condition,
        reference_id=120001,
        created_by="u-test",
    )
    goal = CarePlanGoal(
        id=1,
        care_plan_pk=1,
        tenant_id="org-test",
        reference_reference="Goal/1",
        reference_type=CarePlanGoalReferenceType.Goal,
        reference_id=1,
        created_by="u-test",
    )
    cp = _care_plan(
        title="Diabetes Care Plan",
        description="Comprehensive management of Type 2 Diabetes",
        encounter_reference="Encounter/20001",
        encounter_type=CarePlanEncounterReferenceType.Encounter,
        encounter_id=20001,
        period_start=D,
        period_end=D,
        created=D,
        addresses=[addr],
        goals=[goal],
    )
    out = to_fhir_care_plan(cp)
    assert out["title"] == "Diabetes Care Plan"
    assert out["description"] == "Comprehensive management of Type 2 Diabetes"
    assert out["encounter"]["reference"] == "Encounter/20001"
    assert out["period"]["start"].startswith("2026-01-01T12:00:00")
    assert out["created"].startswith("2026-01-01T12:00:00")
    assert out["addresses"][0]["reference"] == "Condition/120001"
    assert out["goal"][0]["reference"] == "Goal/1"
    assert_valid(care_plan_pb2.CarePlan, out)


def test_care_plan_activity_reference_conforms():
    act = CarePlanActivity(
        id=1,
        care_plan_pk=1,
        tenant_id="org-test",
        reference_reference="ServiceRequest/80001",
        reference_type=CarePlanActivityReferenceType.ServiceRequest,
        reference_id=80001,
        reference_display="Dietitian Consultation",
        created_by="u-test",
    )
    cp = _care_plan(activities=[act])
    out = to_fhir_care_plan(cp)
    assert len(out["activity"]) == 1
    assert out["activity"][0]["reference"]["reference"] == "ServiceRequest/80001"
    assert_valid(care_plan_pb2.CarePlan, out)


def test_care_plan_activity_detail_conforms():
    act = CarePlanActivity(
        id=1,
        care_plan_pk=1,
        tenant_id="org-test",
        detail_kind=CarePlanActivityKind.CommunicationRequest,
        detail_status=CarePlanActivityStatus.in_progress,
        detail_do_not_perform=False,
        detail_scheduled_period_start=D,
        detail_scheduled_period_end=D,
        detail_location_reference="Location/230001",
        detail_location_type=CarePlanLocationReferenceType.Location,
        detail_location_id=230001,
        detail_daily_amount_value=2.0,
        detail_daily_amount_unit="tablets",
        detail_quantity_value=60.0,
        detail_quantity_unit="tablets",
        detail_description="Take twice daily with meals",
        created_by="u-test",
    )
    perf = CarePlanActivityDetailPerformer(
        id=1,
        activity_id=1,
        tenant_id="org-test",
        reference_reference="Practitioner/30001",
        reference_type=CarePlanActivityDetailPerformerReferenceType.Practitioner,
        reference_id=30001,
        created_by="u-test",
    )
    act.detail_performers = [perf]
    cp = _care_plan(activities=[act])
    out = to_fhir_care_plan(cp)
    det = out["activity"][0]["detail"]
    assert det["kind"] == "CommunicationRequest"
    assert det["status"] == "in-progress"
    assert det["doNotPerform"] is False
    assert det["location"]["reference"] == "Location/230001"
    assert det["dailyAmount"]["value"] == 2.0
    assert det["quantity"]["value"] == 60.0
    assert det["performer"][0]["reference"] == "Practitioner/30001"
    assert_valid(care_plan_pb2.CarePlan, out)


def test_care_plan_activity_outcomes_and_progress_conforms():
    act = CarePlanActivity(
        id=1,
        care_plan_pk=1,
        tenant_id="org-test",
        detail_status=CarePlanActivityStatus.completed,
        created_by="u-test",
    )
    occ = CarePlanActivityOutcomeCC(
        id=1,
        activity_id=1,
        tenant_id="org-test",
        text="Met expectation",
        created_by="u-test",
    )
    act.outcome_codeable_concepts = [occ]
    oref = CarePlanActivityOutcomeReference(
        id=1,
        activity_id=1,
        tenant_id="org-test",
        reference_reference="Observation/160001",
        reference_type="Observation",
        reference_id=160001,
        created_by="u-test",
    )
    act.outcome_references = [oref]
    prog = CarePlanActivityProgress(
        id=1,
        activity_id=1,
        tenant_id="org-test",
        text="Patient shows good progress.",
        time=D,
        author_string="Nurse Jane",
        created_by="u-test",
    )
    act.progress = [prog]
    cp = _care_plan(activities=[act])
    out = to_fhir_care_plan(cp)
    act_out = out["activity"][0]
    assert act_out["outcomeCodeableConcept"][0]["text"] == "Met expectation"
    assert act_out["outcomeReference"][0]["reference"] == "Observation/160001"
    assert act_out["progress"][0]["text"] == "Patient shows good progress."
    assert act_out["progress"][0]["authorString"] == "Nurse Jane"
    assert_valid(care_plan_pb2.CarePlan, out)


def test_care_plan_notes_conforms():
    note1 = CarePlanNote(
        id=1,
        care_plan_pk=1,
        tenant_id="org-test",
        text="Patient advised to increase water intake.",
        time=D,
        author_string="Dr. House",
        created_by="u-test",
    )
    note2 = CarePlanNote(
        id=2,
        care_plan_pk=1,
        tenant_id="org-test",
        text="Follow-up scheduled in 2 weeks.",
        time=D,
        author_reference_reference="Practitioner/30001",
        author_reference_type=CarePlanAuthorReferenceType.Practitioner,
        author_reference_id=30001,
        author_reference_display="Dr. Lead",
        created_by="u-test",
    )
    cp = _care_plan(notes=[note1, note2])
    out = to_fhir_care_plan(cp)
    assert len(out["note"]) == 2
    assert out["note"][0]["authorString"] == "Dr. House"
    assert out["note"][1]["authorReference"]["reference"] == "Practitioner/30001"
    assert_valid(care_plan_pb2.CarePlan, out)


@pytest.mark.parametrize(
    "status_val",
    [
        CarePlanStatus.draft,
        CarePlanStatus.active,
        CarePlanStatus.on_hold,
        CarePlanStatus.revoked,
        CarePlanStatus.completed,
        CarePlanStatus.entered_in_error,
        CarePlanStatus.unknown,
    ],
)
def test_all_statuses_conforms(status_val):
    cp = _care_plan(status=status_val)
    out = to_fhir_care_plan(cp)
    assert out["status"] == status_val.value
    assert_valid(care_plan_pb2.CarePlan, out)


@pytest.mark.parametrize(
    "intent_val",
    [
        CarePlanIntent.proposal,
        CarePlanIntent.plan,
        CarePlanIntent.order,
        CarePlanIntent.option,
    ],
)
def test_all_intents_conforms(intent_val):
    cp = _care_plan(intent=intent_val)
    out = to_fhir_care_plan(cp)
    assert out["intent"] == intent_val.value
    assert_valid(care_plan_pb2.CarePlan, out)
