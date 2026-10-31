"""FHIR R4 conformance for `to_fhir_activity_definition()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.
"""

import datetime as dt

import pytest

from app.fhir.mappers.activity_definition import (
    to_fhir_activity_definition,
)
from app.models.activity_definition import (
    ActivityDefinitionAssignerReferenceType,
    ActivityDefinitionBodySite,
    ActivityDefinitionBodySiteCoding,
    ActivityDefinitionCodeCoding,
    ActivityDefinitionContact,
    ActivityDefinitionContactRole,
    ActivityDefinitionContactTelecom,
    ActivityDefinitionDosage,
    ActivityDefinitionDosageRouteCoding,
    ActivityDefinitionDosageSiteCoding,
    ActivityDefinitionDynamicValue,
    ActivityDefinitionIdentifier,
    ActivityDefinitionIdentifierTypeCoding,
    ActivityDefinitionIntent,
    ActivityDefinitionJurisdiction,
    ActivityDefinitionJurisdictionCoding,
    ActivityDefinitionKind,
    ActivityDefinitionModel,
    ActivityDefinitionParticipant,
    ActivityDefinitionParticipantRoleCoding,
    ActivityDefinitionParticipantType,
    ActivityDefinitionPriority,
    ActivityDefinitionRelatedArtifact,
    ActivityDefinitionRelatedArtifactType,
    ActivityDefinitionStatus,
    ActivityDefinitionSubjectCoding,
    ActivityDefinitionTopic,
    ActivityDefinitionTopicCoding,
    ActivityDefinitionUseContext,
)
from app.models.enums import IdentifierUse
from app.schemas.enums import ContactPointSystem, ContactPointUse

from .support import assert_valid

activity_definition_pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.activity_definition_pb2",
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
    "body_sites",
    "code_codings",
    "subject_codings",
    "product_codings",
    "related_artifacts",
    "participants",
    "dosages",
    "dynamic_values",
    "specimen_requirements",
    "observation_requirements",
    "observation_result_requirements",
)


def _activity_definition(**overrides) -> ActivityDefinitionModel:
    fields = {
        "id": 1,
        "activity_definition_id": 410001,
        "tenant_id": "org-test",
        "status": ActivityDefinitionStatus.draft,
        "name": "BloodGlucoseMonitoringActivity",
        "title": "Blood Glucose Monitoring Activity",
        "kind": ActivityDefinitionKind.ServiceRequest,
        "intent": ActivityDefinitionIntent.order,
        "priority": ActivityDefinitionPriority.routine,
        "do_not_perform": False,
        "created_by": "u-test",
        "created_at": D,
        "updated_at": D,
        "extension": [],
    }
    fields.update(overrides)
    ad = ActivityDefinitionModel(**fields)
    for attr in _CHILD_ATTRS:
        if getattr(ad, attr, None) is None:
            setattr(ad, attr, [])
    return ad


def test_minimal_activity_definition_conforms():
    ad = _activity_definition()
    out = to_fhir_activity_definition(ad)
    assert out["resourceType"] == "ActivityDefinition"
    assert out["id"] == "410001"
    assert out["status"] == "draft"
    assert out["name"] == "BloodGlucoseMonitoringActivity"
    assert out["title"] == "Blood Glucose Monitoring Activity"
    assert out["kind"] == "ServiceRequest"
    assert out["intent"] == "order"
    assert out["priority"] == "routine"
    assert out["doNotPerform"] is False
    assert_valid(activity_definition_pb2.ActivityDefinition, out)


def test_activity_definition_identifiers_conforms():
    ident = ActivityDefinitionIdentifier(
        id=1,
        activity_definition_pk=1,
        tenant_id="org-test",
        use=IdentifierUse.official,
        type_text="Definition ID",
        system="http://example.org/act-def",
        value="AD-999",
        period_start=D,
        period_end=D,
        assigner_reference="Organization/190001",
        assigner_type=ActivityDefinitionAssignerReferenceType.Organization,
        assigner_id=190001,
        assigner_display="Acme Hospital",
        created_by="u-test",
    )
    ident.type_codings = [
        ActivityDefinitionIdentifierTypeCoding(
            id=1,
            identifier_id=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/v2-0203",
            code="PLAC",
            display="Placer Identifier",
            created_by="u-test",
        )
    ]
    ad = _activity_definition(identifiers=[ident])
    out = to_fhir_activity_definition(ad)
    assert len(out["identifier"]) == 1
    i = out["identifier"][0]
    assert i["use"] == "official"
    assert i["value"] == "AD-999"
    assert i["system"] == "http://example.org/act-def"
    assert i["type"]["text"] == "Definition ID"
    assert i["assigner"]["reference"] == "Organization/190001"
    assert_valid(activity_definition_pb2.ActivityDefinition, out)


def test_activity_definition_contacts_conforms():
    c = ActivityDefinitionContact(
        id=1,
        activity_definition_pk=1,
        tenant_id="org-test",
        role=ActivityDefinitionContactRole.contact,
        name="Clinical Protocols Committee",
        created_by="u-test",
    )
    c.telecoms = [
        ActivityDefinitionContactTelecom(
            id=1,
            activity_definition_contact_id=1,
            tenant_id="org-test",
            system=ContactPointSystem.email,
            value="protocols@example.org",
            use=ContactPointUse.work,
            rank=1,
            created_by="u-test",
        )
    ]
    author = ActivityDefinitionContact(
        id=2,
        activity_definition_pk=1,
        tenant_id="org-test",
        role=ActivityDefinitionContactRole.author,
        name="Dr. Author",
        created_by="u-test",
    )
    author.telecoms = []

    ad = _activity_definition(contacts=[c, author])
    out = to_fhir_activity_definition(ad)
    assert len(out["contact"]) == 1
    assert out["contact"][0]["name"] == "Clinical Protocols Committee"
    assert out["contact"][0]["telecom"][0]["value"] == "protocols@example.org"
    assert len(out["author"]) == 1
    assert out["author"][0]["name"] == "Dr. Author"
    assert_valid(activity_definition_pb2.ActivityDefinition, out)


def test_activity_definition_use_context_and_jurisdiction_conforms():
    uc = ActivityDefinitionUseContext(
        id=1,
        activity_definition_pk=1,
        tenant_id="org-test",
        system="http://terminology.hl7.org/CodeSystem/usage-context-type",
        code="venue",
        display="Clinical Venue",
        value_codeable_concept_text="Inpatient",
        created_by="u-test",
    )
    uc.value_codings = []

    jur = ActivityDefinitionJurisdiction(
        id=1,
        activity_definition_pk=1,
        tenant_id="org-test",
        text="US",
        created_by="u-test",
    )
    jur.codings = [
        ActivityDefinitionJurisdictionCoding(
            id=1,
            activity_definition_jurisdiction_id=1,
            tenant_id="org-test",
            system="urn:iso:std:iso:3166",
            code="US",
            display="United States of America",
            created_by="u-test",
        )
    ]

    top = ActivityDefinitionTopic(
        id=1,
        activity_definition_pk=1,
        tenant_id="org-test",
        text="Endocrinology",
        created_by="u-test",
    )
    top.codings = [
        ActivityDefinitionTopicCoding(
            id=1,
            activity_definition_topic_id=1,
            tenant_id="org-test",
            system="http://snomed.info/sct",
            code="394583002",
            display="Endocrinology",
            created_by="u-test",
        )
    ]

    ad = _activity_definition(
        use_contexts=[uc],
        jurisdictions=[jur],
        topics=[top],
        approval_date=D_DATE,
        last_review_date=D_DATE,
    )
    out = to_fhir_activity_definition(ad)
    assert len(out["useContext"]) == 1
    assert out["useContext"][0]["code"]["code"] == "venue"
    assert out["useContext"][0]["valueCodeableConcept"]["text"] == "Inpatient"
    assert len(out["jurisdiction"]) == 1
    assert out["jurisdiction"][0]["coding"][0]["code"] == "US"
    assert len(out["topic"]) == 1
    assert out["topic"][0]["coding"][0]["code"] == "394583002"
    assert out["approvalDate"] == "2026-01-01"
    assert out["lastReviewDate"] == "2026-01-01"
    assert_valid(activity_definition_pb2.ActivityDefinition, out)


def test_activity_definition_full_conforms():
    # participant
    part = ActivityDefinitionParticipant(
        id=1,
        activity_definition_pk=1,
        tenant_id="org-test",
        type=ActivityDefinitionParticipantType.practitioner,
        role_text="Primary Nurse",
        created_by="u-test",
    )
    part.role_codings = [
        ActivityDefinitionParticipantRoleCoding(
            id=1,
            activity_definition_participant_id=1,
            tenant_id="org-test",
            system="http://snomed.info/sct",
            code="224535009",
            display="Registered nurse",
            created_by="u-test",
        )
    ]

    # dosage
    dosage = ActivityDefinitionDosage(
        id=1,
        activity_definition_pk=1,
        tenant_id="org-test",
        sequence=1,
        text="Take 1 tablet daily",
        patient_instruction="Take with food",
        timing={"repeat": {"frequency": 1, "period": 1, "periodUnit": "d"}},
        as_needed_boolean=False,
        site_text="Oral",
        route_text="Oral",
        method_text="Swallow",
        created_by="u-test",
    )
    dosage.site_codings = [
        ActivityDefinitionDosageSiteCoding(
            id=1,
            activity_definition_dosage_id=1,
            tenant_id="org-test",
            system="http://snomed.info/sct",
            code="181220002",
            display="Entire oral cavity",
            created_by="u-test",
        )
    ]
    dosage.route_codings = [
        ActivityDefinitionDosageRouteCoding(
            id=1,
            activity_definition_dosage_id=1,
            tenant_id="org-test",
            system="http://snomed.info/sct",
            code="260548002",
            display="Oral",
            created_by="u-test",
        )
    ]
    dosage.method_codings = []
    dosage.as_needed_codings = []

    # body site
    bs = ActivityDefinitionBodySite(
        id=1,
        activity_definition_pk=1,
        tenant_id="org-test",
        text="Left Arm",
        created_by="u-test",
    )
    bs.codings = [
        ActivityDefinitionBodySiteCoding(
            id=1,
            activity_definition_body_site_id=1,
            tenant_id="org-test",
            system="http://snomed.info/sct",
            code="368208006",
            display="Left upper arm structure",
            created_by="u-test",
        )
    ]

    # related artifact
    ra = ActivityDefinitionRelatedArtifact(
        id=1,
        activity_definition_pk=1,
        tenant_id="org-test",
        type=ActivityDefinitionRelatedArtifactType.documentation,
        label="Guideline",
        display="ADA 2026 Standards of Care",
        url="https://diabetesjournals.org/care",
        created_by="u-test",
    )

    # dynamic value
    dv = ActivityDefinitionDynamicValue(
        id=1,
        activity_definition_pk=1,
        tenant_id="org-test",
        path="priority",
        expression_description="Dynamic priority",
        expression_language="text/cql",
        expression_expression="CalculatePriority()",
        created_by="u-test",
    )

    code_coding = ActivityDefinitionCodeCoding(
        id=1,
        activity_definition_pk=1,
        tenant_id="org-test",
        system="http://snomed.info/sct",
        code="35335000",
        display="Blood glucose measurement",
        created_by="u-test",
    )

    subj_coding = ActivityDefinitionSubjectCoding(
        id=1,
        activity_definition_pk=1,
        tenant_id="org-test",
        system="http://snomed.info/sct",
        code="116154003",
        display="Patient",
        created_by="u-test",
    )

    ad = _activity_definition(
        code_text="Blood glucose measurement",
        code_codings=[code_coding],
        subject_codeable_concept_text="Patient",
        subject_codings=[subj_coding],
        participants=[part],
        dosages=[dosage],
        body_sites=[bs],
        related_artifacts=[ra],
        dynamic_values=[dv],
        timing_date_time=D,
        extension=[{"url": "http://example.org/ext", "valueString": "custom"}],
    )
    out = to_fhir_activity_definition(ad)
    assert out["code"]["coding"][0]["code"] == "35335000"
    assert out["subjectCodeableConcept"]["coding"][0]["code"] == "116154003"
    assert len(out["participant"]) == 1
    assert out["participant"][0]["type"] == "practitioner"
    assert len(out["dosage"]) == 1
    assert out["dosage"][0]["sequence"] == 1
    assert len(out["bodySite"]) == 1
    assert len(out["relatedArtifact"]) == 1
    assert len(out["dynamicValue"]) == 1
    assert out["dynamicValue"][0]["expression"]["expression"] == "CalculatePriority()"
    assert len(out["extension"]) == 1
    assert_valid(activity_definition_pb2.ActivityDefinition, out)
