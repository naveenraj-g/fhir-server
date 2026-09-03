"""FHIR R4 conformance for `to_fhir_organization()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.
"""

import datetime as dt

import pytest

from app.fhir.mappers.organization import to_fhir_organization
from app.models.organization import (
    OrganizationAddress,
    OrganizationAlias,
    OrganizationContact,
    OrganizationContactTelecom,
    OrganizationEndpoint,
    OrganizationIdentifier,
    OrganizationModel,
    OrganizationTelecom,
    OrganizationType,
)

from .support import assert_valid, fhir_json_text

organization_pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.organization_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)

_CHILD_ATTRS = (
    "identifiers", "types", "aliases", "telecoms", "addresses", "contacts",
    "endpoints",
)


def _org(**overrides) -> OrganizationModel:
    """An Organization carrying only the columns the model marks NOT NULL,
    plus empty sub-resource lists (nothing is lazy-loadable off a session
    here). active/name are both NOT NULL, so every shape under test must
    carry them."""
    fields = {
        "organization_id": 190001,
        "org_id": "org-test",
        "active": True,
        "name": "Acme Health",
        "created_by": "u-test",
        "created_at": D,
    }
    fields.update(overrides)
    org = OrganizationModel(**fields)
    for attr in _CHILD_ATTRS:
        if getattr(org, attr, None) is None:
            setattr(org, attr, [])
    return org


def _with(attr, *rows) -> OrganizationModel:
    org = _org()
    setattr(org, attr, list(rows))
    return org


def _identifier(**kw) -> OrganizationIdentifier:
    return OrganizationIdentifier(
        **{
            "id": 1, "org_id": "org-test", "system": "http://ex.org/ids",
            "value": "ORG-1", "created_by": "u-test", "created_at": D, **kw,
        }
    )


def _type(**kw) -> OrganizationType:
    return OrganizationType(
        **{
            "id": 1, "org_id": "org-test",
            "coding_system": "http://terminology.hl7.org/CodeSystem/organization-type",
            "coding_code": "prov", "coding_display": "Healthcare Provider",
            "created_by": "u-test", "created_at": D, **kw,
        }
    )


def _alias(**kw) -> OrganizationAlias:
    return OrganizationAlias(
        **{
            "id": 1, "org_id": "org-test", "value": "Acme",
            "created_by": "u-test", "created_at": D, **kw,
        }
    )


def _telecom(**kw) -> OrganizationTelecom:
    return OrganizationTelecom(
        **{
            "id": 1, "org_id": "org-test", "system": "phone", "value": "555-1234",
            "created_by": "u-test", "created_at": D, **kw,
        }
    )


def _address(**kw) -> OrganizationAddress:
    return OrganizationAddress(
        **{
            "id": 1, "org_id": "org-test", "type": "both", "city": "Amsterdam",
            "state": "NH", "postal_code": "1000 AA", "country": "NLD",
            "created_by": "u-test", "created_at": D, **kw,
        }
    )


def _endpoint(**kw) -> OrganizationEndpoint:
    return OrganizationEndpoint(
        **{
            "id": 1, "org_id": "org-test",
            "created_by": "u-test", "created_at": D, **kw,
        }
    )


def _contact(*, telecoms=None, **kw) -> OrganizationContact:
    """An OrganizationContact row with its `telecoms` grandchild list always
    set explicitly — nothing lazy-loads off a detached instance here."""
    c = OrganizationContact(
        **{
            "id": 1, "org_id": "org-test", "address_type": "both",
            "address_city": "Amsterdam", "address_state": "NH",
            "address_postal_code": "1000 AA", "address_country": "NLD",
            "created_by": "u-test", "created_at": D, **kw,
        }
    )
    c.telecoms = list(telecoms) if telecoms else []
    return c


# Each case is one distinct shape the mapper can emit. Anything with a
# conditional branch in app/fhir/mappers/organization/fhir.py should appear here.
CASES = {
    "minimal": _org(),

    "active_false": _org(active=False),

    "partof_resolved": _org(
        partof_type="Organization", partof_id=190000, partof_display="Acme Group"
    ),
    "partof_identifier_fallback": _org(
        partof_identifier_system="urn:org-registry",
        partof_identifier_value="ORG-9",
        partof_identifier_use="official",
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
            assigner_type="Organization", assigner_id=190002, assigner_display="Acme"
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

    "type_with_text": _with(
        "types",
        _type(
            coding_system="http://terminology.hl7.org/CodeSystem/organization-type",
            coding_version="2.0",
            coding_code="prov",
            coding_display="Healthcare Provider",
            text="Healthcare Provider",
            coding_user_selected=True,
        ),
    ),
    "type_multiple": _with(
        "types",
        _type(id=1, coding_code="prov", coding_display="Healthcare Provider"),
        _type(id=2, coding_code="ins", coding_display="Insurance Company"),
    ),

    "alias_multiple": _with(
        "aliases",
        *[
            OrganizationAlias(id=i, org_id="org-test", value=v, created_by="u-test", created_at=D)
            for i, v in enumerate(["Acme Health Group", "AHG"], 1)
        ],
    ),

    "telecoms_with_rank_and_period": _with(
        "telecoms",
        _telecom(
            id=1, system="phone", value="2328", use="work", rank=1,
            period_start=D, period_end=D,
        ),
        _telecom(id=2, system="email", value="a@b.example"),
    ),

    "address_full": _with(
        "addresses",
        _address(
            use="work", type="both", text="Galapagosweg 91, Building A",
            line="Galapagosweg 91, Building A", district="Texel",
            period_start=D, period_end=D,
        ),
    ),

    "contact_purpose_name_address_telecom": _with(
        "contacts",
        _contact(
            purpose_system="http://terminology.hl7.org/CodeSystem/contactentity-type",
            purpose_code="ADMIN",
            purpose_display="Administrative",
            purpose_text="Administrative",
            name_use="official",
            name_text="Mr. Denny Denwiddie",
            name_family="Denwiddie",
            name_given="Denny",
            name_prefix="Mr.",
            name_period_start=D,
            name_period_end=D,
            address_use="work",
            address_text="Galapagosweg 91, Building A",
            address_line="Galapagosweg 91, Building A",
            address_district="Texel",
            address_period_start=D,
            address_period_end=D,
            telecoms=[
                OrganizationContactTelecom(
                    id=1, org_id="org-test", system="phone", value="022-655 2321",
                    use="work", rank=1, created_by="u-test", created_at=D,
                ),
            ],
        ),
    ),
    "contact_minimal": _with("contacts", _contact()),

    "endpoint_resolved": _with(
        "endpoints",
        _endpoint(
            reference_type="Endpoint", reference_id=7, reference_display="Main endpoint"
        ),
    ),
    "endpoint_identifier_fallback": _with(
        "endpoints",
        _endpoint(
            reference_identifier_system="urn:ext-endpoint",
            reference_identifier_value="EP-1",
        ),
    ),
}


@pytest.mark.parametrize("case", sorted(CASES), ids=sorted(CASES))
def test_organization_mapper_emits_valid_fhir_r4(case):
    assert_valid(organization_pb2.Organization, to_fhir_organization(CASES[case]))


# ── Guarding the oracle ────────────────────────────────────────────────────────
# If google-fhir-r4 ever stops validating — a version bump, a changed API, a
# silently-swallowed error — every test above would keep passing while checking
# nothing. These deliberately-broken payloads prove the check still has teeth.

@pytest.mark.parametrize(
    "label,broken",
    [
        ("active as string not boolean", {"active": "yes"}),
        ("misspelled element", {"nam3": "Acme Health"}),
        ("identifier as string not object", {"identifier": ["ORG-1"]}),
        ("type as strings not CodeableConcepts", {"type": ["prov"]}),
        ("alias as objects not strings", {"alias": [{"value": "Acme"}]}),
        ("partOf as string not Reference", {"partOf": "Organization/190000"}),
        ("contact.address as string not Address", {"contact": [{"address": "somewhere"}]}),
    ],
)
def test_validator_rejects_invalid_fhir(label, broken):
    from google.fhir.r4 import json_format

    payload = {
        "resourceType": "Organization", "id": "190001", "active": True,
        "name": "Acme Health", **broken,
    }
    with pytest.raises(Exception):  # noqa: B017 — the library raises several types
        json_format.json_fhir_string_to_proto(
            fhir_json_text(payload), organization_pb2.Organization, validate=True
        )
