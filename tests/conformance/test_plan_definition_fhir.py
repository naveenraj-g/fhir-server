"""FHIR R4 conformance for `to_fhir_plan_definition()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.
"""

import datetime as dt

import pytest

from app.fhir.mappers.plan_definition import to_fhir_plan_definition
from app.models.enums import IdentifierUse, OrganizationReferenceType
from app.models.plan_definition import (
    PlanDefinitionAction,
    PlanDefinitionActionCardinalityBehavior,
    PlanDefinitionActionGroupingBehavior,
    PlanDefinitionActionPrecheckBehavior,
    PlanDefinitionActionPriority,
    PlanDefinitionActionRequiredBehavior,
    PlanDefinitionActionSelectionBehavior,
    PlanDefinitionActionTypeCoding,
    PlanDefinitionContact,
    PlanDefinitionContactRole,
    PlanDefinitionContactTelecom,
    PlanDefinitionGoal,
    PlanDefinitionGoalCategoryCoding,
    PlanDefinitionGoalDescriptionCoding,
    PlanDefinitionGoalPriorityCoding,
    PlanDefinitionGoalStartCoding,
    PlanDefinitionIdentifier,
    PlanDefinitionIdentifierTypeCoding,
    PlanDefinitionJurisdiction,
    PlanDefinitionJurisdictionCoding,
    PlanDefinitionModel,
    PlanDefinitionRelatedArtifact,
    PlanDefinitionRelatedArtifactType,
    PlanDefinitionStatus,
    PlanDefinitionSubjectCoding,
    PlanDefinitionSubjectReferenceType,
    PlanDefinitionTopic,
    PlanDefinitionTopicCoding,
    PlanDefinitionTypeCoding,
    PlanDefinitionUseContext,
    PlanDefinitionUseContextValueCoding,
)
from app.schemas.enums import ContactPointSystem, ContactPointUse

from .support import assert_valid

plan_definition_pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.plan_definition_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, 12, 0, 0, tzinfo=dt.timezone.utc)
D_DATE = dt.date(2026, 1, 1)

_CHILD_ATTRS = (
    "identifiers",
    "contacts",
    "use_contexts",
    "jurisdictions",
    "topics",
    "related_artifacts",
    "type_codings",
    "subject_codings",
    "goals",
    "actions",
)


def _plan_definition(**overrides) -> PlanDefinitionModel:
    fields = {
        "id": 1,
        "plan_definition_id": 420001,
        "tenant_id": "org-test",
        "status": PlanDefinitionStatus.draft,
        "name": "DiabetesCareProtocol",
        "title": "Diabetes Care Protocol",
        "experimental": False,
        "created_by": "u-test",
        "created_at": D,
        "updated_at": D,
        "extension": [],
        "library": [],
    }
    fields.update(overrides)
    pd = PlanDefinitionModel(**fields)
    for attr in _CHILD_ATTRS:
        if getattr(pd, attr, None) is None:
            setattr(pd, attr, [])
    return pd


def test_minimal_plan_definition_conforms():
    pd = _plan_definition()
    out = to_fhir_plan_definition(pd)
    assert out["resourceType"] == "PlanDefinition"
    assert out["id"] == "420001"
    assert out["status"] == "draft"
    assert out["name"] == "DiabetesCareProtocol"
    assert out["title"] == "Diabetes Care Protocol"
    assert out["experimental"] is False
    assert_valid(plan_definition_pb2.PlanDefinition, out)


def test_plan_definition_identifiers_conforms():
    ident = PlanDefinitionIdentifier(
        id=1,
        plan_definition_pk=1,
        tenant_id="org-test",
        use=IdentifierUse.official,
        type_text="Protocol ID",
        system="http://example.org/plan-def",
        value="PLAN-101",
        period_start=D,
        period_end=D,
        assigner_reference="Organization/190001",
        assigner_type=OrganizationReferenceType.Organization,
        assigner_id=190001,
        assigner_display="Acme Hospital",
        created_by="u-test",
    )
    ident.type_codings = [
        PlanDefinitionIdentifierTypeCoding(
            id=1,
            identifier_id=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/v2-0203",
            code="PLAC",
            display="Placer Identifier",
            created_by="u-test",
        )
    ]
    pd = _plan_definition(identifiers=[ident])
    out = to_fhir_plan_definition(pd)
    assert len(out["identifier"]) == 1
    i = out["identifier"][0]
    assert i["use"] == "official"
    assert i["value"] == "PLAN-101"
    assert i["system"] == "http://example.org/plan-def"
    assert i["type"]["text"] == "Protocol ID"
    assert i["assigner"]["reference"] == "Organization/190001"
    assert_valid(plan_definition_pb2.PlanDefinition, out)


def test_plan_definition_contacts_conforms():
    c = PlanDefinitionContact(
        id=1,
        plan_definition_pk=1,
        tenant_id="org-test",
        role=PlanDefinitionContactRole.contact,
        name="Clinical Guidelines Committee",
        created_by="u-test",
    )
    c.telecoms = [
        PlanDefinitionContactTelecom(
            id=1,
            plan_definition_contact_id=1,
            tenant_id="org-test",
            system=ContactPointSystem.email,
            value="guidelines@example.org",
            use=ContactPointUse.work,
            rank=1,
            created_by="u-test",
        )
    ]
    author = PlanDefinitionContact(
        id=2,
        plan_definition_pk=1,
        tenant_id="org-test",
        role=PlanDefinitionContactRole.author,
        name="Dr. Specialist",
        created_by="u-test",
    )
    author.telecoms = []

    pd = _plan_definition(contacts=[c, author])
    out = to_fhir_plan_definition(pd)
    assert len(out["contact"]) == 1
    assert out["contact"][0]["name"] == "Clinical Guidelines Committee"
    assert out["contact"][0]["telecom"][0]["value"] == "guidelines@example.org"
    assert len(out["author"]) == 1
    assert out["author"][0]["name"] == "Dr. Specialist"
    assert_valid(plan_definition_pb2.PlanDefinition, out)


def test_plan_definition_use_context_jurisdiction_topics_conforms():
    uc = PlanDefinitionUseContext(
        id=1,
        plan_definition_pk=1,
        tenant_id="org-test",
        system="http://terminology.hl7.org/CodeSystem/usage-context-type",
        code="venue",
        display="Clinical Venue",
        value_codeable_concept_text="Outpatient",
        created_by="u-test",
    )
    uc.value_codings = []

    jur = PlanDefinitionJurisdiction(
        id=1,
        plan_definition_pk=1,
        tenant_id="org-test",
        text="US",
        created_by="u-test",
    )
    jur.codings = [
        PlanDefinitionJurisdictionCoding(
            id=1,
            plan_definition_jurisdiction_id=1,
            tenant_id="org-test",
            system="urn:iso:std:iso:3166",
            code="US",
            display="United States of America",
            created_by="u-test",
        )
    ]

    top = PlanDefinitionTopic(
        id=1,
        plan_definition_pk=1,
        tenant_id="org-test",
        text="Endocrinology",
        created_by="u-test",
    )
    top.codings = [
        PlanDefinitionTopicCoding(
            id=1,
            plan_definition_topic_id=1,
            tenant_id="org-test",
            system="http://snomed.info/sct",
            code="394583002",
            display="Endocrinology",
            created_by="u-test",
        )
    ]

    art = PlanDefinitionRelatedArtifact(
        id=1,
        plan_definition_pk=1,
        tenant_id="org-test",
        type=PlanDefinitionRelatedArtifactType.documentation,
        display="ADA Guidelines 2026",
        url="https://diabetesjournals.org/care",
        created_by="u-test",
    )

    pd = _plan_definition(
        use_contexts=[uc],
        jurisdictions=[jur],
        topics=[top],
        related_artifacts=[art],
    )
    out = to_fhir_plan_definition(pd)
    assert len(out["useContext"]) == 1
    assert out["useContext"][0]["code"]["code"] == "venue"
    assert len(out["jurisdiction"]) == 1
    assert out["jurisdiction"][0]["coding"][0]["code"] == "US"
    assert len(out["topic"]) == 1
    assert out["topic"][0]["text"] == "Endocrinology"
    assert len(out["relatedArtifact"]) == 1
    assert out["relatedArtifact"][0]["type"] == "documentation"
    assert_valid(plan_definition_pb2.PlanDefinition, out)


def test_plan_definition_goals_conforms():
    goal = PlanDefinitionGoal(
        id=1,
        plan_definition_pk=1,
        tenant_id="org-test",
        goal_id="hba1c-goal",
        category_text="Biochemical",
        description_text="Maintain HbA1c below 7.0%",
        priority_text="High",
        start_text="Upon diagnosis",
        addresses=[{"text": "Type 2 Diabetes Mellitus"}],
        documentation=[{"type": "citation", "display": "Clinical standard"}],
        target=[
            {
                "measure": {"text": "HbA1c"},
                "detailQuantity": {
                    "value": 7.0,
                    "comparator": "<",
                    "unit": "%",
                    "system": "http://unitsofmeasure.org",
                    "code": "%",
                },
            }
        ],
        created_by="u-test",
    )
    goal.category_codings = []
    goal.description_codings = []
    goal.priority_codings = []
    goal.start_codings = []

    pd = _plan_definition(goals=[goal])
    out = to_fhir_plan_definition(pd)
    assert len(out["goal"]) == 1
    g = out["goal"][0]
    assert g["id"] == "hba1c-goal"
    assert g["description"]["text"] == "Maintain HbA1c below 7.0%"
    assert g["priority"]["text"] == "High"
    assert len(g["target"]) == 1
    assert g["target"][0]["detailQuantity"]["value"] == 7.0
    assert_valid(plan_definition_pb2.PlanDefinition, out)


def test_plan_definition_actions_recursive_conforms():
    parent_act = PlanDefinitionAction(
        id=10,
        plan_definition_pk=1,
        parent_action_id=None,
        action_id_str="step-1",
        prefix="1",
        title="Initial Assessment",
        description="Check baseline labs",
        text_equivalent="Patient needs initial lab testing",
        priority=PlanDefinitionActionPriority.routine,
        code=[{"text": "LabPanel"}],
        goal_id=["hba1c-goal"],
        grouping_behavior=PlanDefinitionActionGroupingBehavior.logical_group,
        selection_behavior=PlanDefinitionActionSelectionBehavior.all,
        required_behavior=PlanDefinitionActionRequiredBehavior.must,
        precheck_behavior=PlanDefinitionActionPrecheckBehavior.yes,
        cardinality_behavior=PlanDefinitionActionCardinalityBehavior.single,
        definition_canonical="http://example.org/ActivityDefinition/lab-panel",
        tenant_id="org-test",
        created_by="u-test",
    )
    parent_act.type_codings = []

    child_act = PlanDefinitionAction(
        id=11,
        plan_definition_pk=1,
        parent_action_id=10,
        action_id_str="step-1-1",
        prefix="1.1",
        title="Order HbA1c",
        priority=PlanDefinitionActionPriority.routine,
        definition_canonical="http://example.org/ActivityDefinition/hba1c-test",
        tenant_id="org-test",
        created_by="u-test",
    )
    child_act.type_codings = []

    pd = _plan_definition(actions=[parent_act, child_act])
    out = to_fhir_plan_definition(pd)
    assert len(out["action"]) == 1
    top = out["action"][0]
    assert top["id"] == "step-1"
    assert top["prefix"] == "1"
    assert top["title"] == "Initial Assessment"
    assert top["goalId"] == ["hba1c-goal"]
    assert top["groupingBehavior"] == "logical-group"
    assert top["selectionBehavior"] == "all"
    assert "action" in top
    assert len(top["action"]) == 1
    child = top["action"][0]
    assert child["id"] == "step-1-1"
    assert child["prefix"] == "1.1"
    assert child["title"] == "Order HbA1c"
    assert_valid(plan_definition_pb2.PlanDefinition, out)
