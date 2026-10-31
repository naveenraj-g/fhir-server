"""FHIR R4 conformance for `to_fhir_consent()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.
"""

import datetime as dt

import pytest

from app.fhir.mappers.consent import to_fhir_consent
from app.models.consent import (
    ConsentCategory,
    ConsentCategoryCoding,
    ConsentDataMeaning,
    ConsentIdentifier,
    ConsentIdentifierTypeCoding,
    ConsentModel,
    ConsentOrganization,
    ConsentPatientReferenceType,
    ConsentPerformer,
    ConsentPerformerReferenceType,
    ConsentPolicy,
    ConsentPolicyRuleCoding,
    ConsentProvision,
    ConsentProvisionAction,
    ConsentProvisionActionCoding,
    ConsentProvisionActor,
    ConsentProvisionActorReferenceType,
    ConsentProvisionActorRoleCoding,
    ConsentProvisionClass,
    ConsentProvisionCode,
    ConsentProvisionCodeCoding,
    ConsentProvisionData,
    ConsentProvisionPurpose,
    ConsentProvisionSecurityLabel,
    ConsentProvisionType,
    ConsentScopeCoding,
    ConsentSourceReferenceType,
    ConsentStatus,
    ConsentVerification,
    ConsentVerifiedWithReferenceType,
)
from app.models.enums import IdentifierUse, OrganizationReferenceType

from .support import assert_valid

consent_pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.consent_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, 12, 0, 0, tzinfo=dt.timezone.utc)

_CHILD_ATTRS = (
    "identifiers",
    "scope_codings",
    "categories",
    "performers",
    "organizations",
    "policies",
    "policy_rule_codings",
    "verifications",
    "provisions",
)


def _consent(**overrides) -> ConsentModel:
    fields = {
        "id": 1,
        "consent_id": 440001,
        "tenant_id": "org-test",
        "status": ConsentStatus.active,
        "scope_text": "Privacy Consent",
        "patient_reference": "Patient/10001",
        "patient_type": ConsentPatientReferenceType.Patient,
        "patient_id": 10001,
        "patient_display": "John Doe",
        "date_time": D,
        "created_by": "u-test",
        "updated_at": D,
    }
    children = {attr: overrides.pop(attr, []) for attr in _CHILD_ATTRS}
    fields.update(overrides)
    m = ConsentModel(**fields)

    # By default, add a minimal category and scope coding so R4 required fields are present
    if "scope_codings" not in children or not children["scope_codings"]:
        children["scope_codings"] = [
            ConsentScopeCoding(
                consent_pk=1,
                tenant_id="org-test",
                system="http://terminology.hl7.org/CodeSystem/consentscope",
                code="patient-privacy",
                display="Privacy Consent",
                created_by="u-test",
            )
        ]

    if "categories" not in children or not children["categories"]:
        cat = ConsentCategory(
            consent_pk=1,
            tenant_id="org-test",
            text="Information Access",
            created_by="u-test",
        )
        cat.codings = [
            ConsentCategoryCoding(
                category_id=1,
                tenant_id="org-test",
                system="http://terminology.hl7.org/CodeSystem/v3-ActCode",
                code="INFA",
                display="information access",
                created_by="u-test",
            )
        ]
        children["categories"] = [cat]

    for attr, val in children.items():
        setattr(m, attr, val)
    return m


def test_consent_minimal_conformance():
    m = _consent()
    fhir = to_fhir_consent(m)
    assert_valid(consent_pb2.Consent, fhir)


def test_consent_statuses_conformance():
    for status in ConsentStatus:
        m = _consent(status=status)
        fhir = to_fhir_consent(m)
        assert_valid(consent_pb2.Consent, fhir)


def test_consent_identifiers_conformance():
    ident = ConsentIdentifier(
        consent_pk=1,
        tenant_id="org-test",
        use=IdentifierUse.official,
        type_text="Consent ID",
        system="http://example.org/consents",
        value="CONSENT-12345",
        period_start=D,
        period_end=D + dt.timedelta(days=365),
        assigner_reference="Organization/190001",
        assigner_type=OrganizationReferenceType.Organization,
        assigner_id=190001,
        assigner_display="National Registry",
        created_by="u-test",
    )
    ident.type_codings = [
        ConsentIdentifierTypeCoding(
            identifier_id=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/v2-0203",
            code="TAX",
            display="Tax ID",
            created_by="u-test",
        )
    ]
    m = _consent(identifiers=[ident])
    fhir = to_fhir_consent(m)
    assert_valid(consent_pb2.Consent, fhir)


def test_consent_performers_and_organizations_conformance():
    performer = ConsentPerformer(
        consent_pk=1,
        tenant_id="org-test",
        reference_reference="Practitioner/30001",
        reference_type=ConsentPerformerReferenceType.Practitioner,
        reference_id=30001,
        reference_display="Dr. Alice Smith",
        created_by="u-test",
    )
    org = ConsentOrganization(
        consent_pk=1,
        tenant_id="org-test",
        reference_reference="Organization/190001",
        reference_type=OrganizationReferenceType.Organization,
        reference_id=190001,
        reference_display="General Hospital",
        created_by="u-test",
    )
    m = _consent(performers=[performer], organizations=[org])
    fhir = to_fhir_consent(m)
    assert_valid(consent_pb2.Consent, fhir)


def test_consent_source_conformance():
    m1 = _consent(
        source_reference_reference="DocumentReference/320001",
        source_reference_type=ConsentSourceReferenceType.DocumentReference,
        source_reference_id=320001,
        source_reference_display="Signed Consent Document",
    )
    fhir1 = to_fhir_consent(m1)
    assert_valid(consent_pb2.Consent, fhir1)

    m2 = _consent(
        source_attachment={
            "contentType": "application/pdf",
            "title": "Signed Consent PDF",
        }
    )
    fhir2 = to_fhir_consent(m2)
    assert_valid(consent_pb2.Consent, fhir2)


def test_consent_policy_and_verification_conformance():
    policy = ConsentPolicy(
        consent_pk=1,
        tenant_id="org-test",
        authority="http://example.org/fhir/ConsentPolicy",
        uri="http://example.org/fhir/ConsentPolicy/1",
        created_by="u-test",
    )
    rule_coding = ConsentPolicyRuleCoding(
        consent_pk=1,
        tenant_id="org-test",
        system="http://terminology.hl7.org/CodeSystem/v3-ActCode",
        code="OPTIN",
        display="opt-in",
        created_by="u-test",
    )
    verification = ConsentVerification(
        consent_pk=1,
        tenant_id="org-test",
        verified=True,
        verified_with_reference="Patient/10001",
        verified_with_type=ConsentVerifiedWithReferenceType.Patient,
        verified_with_id=10001,
        verified_with_display="John Doe",
        verification_date=D,
        created_by="u-test",
    )
    m = _consent(
        policies=[policy],
        policy_rule_codings=[rule_coding],
        policy_rule_text="opt-in",
        verifications=[verification],
    )
    fhir = to_fhir_consent(m)
    assert_valid(consent_pb2.Consent, fhir)


def test_consent_provision_conformance():
    prov = ConsentProvision(
        id=1,
        consent_pk=1,
        parent_provision_id=None,
        tenant_id="org-test",
        type=ConsentProvisionType.permit,
        period_start=D,
        period_end=D + dt.timedelta(days=365),
        data_period_start=D - dt.timedelta(days=30),
        data_period_end=D,
        created_by="u-test",
    )

    actor = ConsentProvisionActor(
        id=1,
        provision_id=1,
        tenant_id="org-test",
        role_text="Primary Recipient",
        reference_reference="Practitioner/30001",
        reference_type=ConsentProvisionActorReferenceType.Practitioner,
        reference_id=30001,
        reference_display="Dr. Alice Smith",
        created_by="u-test",
    )
    actor.role_codings = [
        ConsentProvisionActorRoleCoding(
            provision_actor_id=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/v3-ParticipationType",
            code="PRCP",
            display="primary recipient",
            created_by="u-test",
        )
    ]
    prov.actors = [actor]

    action = ConsentProvisionAction(
        id=1,
        provision_id=1,
        tenant_id="org-test",
        text="Access",
        created_by="u-test",
    )
    action.codings = [
        ConsentProvisionActionCoding(
            action_id=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/consentaction",
            code="access",
            display="Access",
            created_by="u-test",
        )
    ]
    prov.actions = [action]

    prov.security_labels = [
        ConsentProvisionSecurityLabel(
            provision_id=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/v3-Confidentiality",
            code="N",
            display="normal",
            created_by="u-test",
        )
    ]

    prov.purposes = [
        ConsentProvisionPurpose(
            provision_id=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/v3-ActReason",
            code="TREAT",
            display="treatment",
            created_by="u-test",
        )
    ]

    prov.classes = [
        ConsentProvisionClass(
            provision_id=1,
            tenant_id="org-test",
            system="http://hl7.org/fhir/resource-types",
            code="Observation",
            display="Observation",
            created_by="u-test",
        )
    ]

    code = ConsentProvisionCode(
        id=1,
        provision_id=1,
        tenant_id="org-test",
        text="Common cold",
        created_by="u-test",
    )
    code.codings = [
        ConsentProvisionCodeCoding(
            code_id=1,
            tenant_id="org-test",
            system="http://snomed.info/sct",
            code="82272006",
            display="Common cold",
            created_by="u-test",
        )
    ]
    prov.codes = [code]

    prov.data_entries = [
        ConsentProvisionData(
            id=1,
            provision_id=1,
            tenant_id="org-test",
            meaning=ConsentDataMeaning.instance,
            reference_reference="Observation/160001",
            reference_type="Observation",
            reference_id=160001,
            reference_display="Blood Glucose",
            created_by="u-test",
        )
    ]

    # Nested sub-provision
    sub = ConsentProvision(
        id=2,
        consent_pk=1,
        parent_provision_id=1,
        tenant_id="org-test",
        type=ConsentProvisionType.deny,
        created_by="u-test",
    )
    sub.actors = []
    sub.actions = []
    sub.security_labels = []
    sub.purposes = []
    sub.classes = []
    sub.codes = []
    sub.data_entries = []
    sub.sub_provisions = []
    prov.sub_provisions = [sub]

    m = _consent(provisions=[prov, sub])
    fhir = to_fhir_consent(m)
    assert_valid(consent_pb2.Consent, fhir)
