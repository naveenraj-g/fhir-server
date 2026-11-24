"""Every rebuilt resource against HL7's own R4 definitions (the `hl7.fhir.r4.core` package that
google-fhir-r4 ships, version 4.0.1 - the same data the spec pages are generated from).

1. **Search parameters.** A resource serves exactly the search parameters its R4 page lists. (HL7's
   package also defines parameters on *extensions* - Patient `mothersMaidenName`, Observation
   `gene-*`, ... - which are not on the resource page and are not served.)
2. **Required-binding codes are Postgres enums.** A search parameter that reads an element of type
   `code` with a *required* binding (a closed list no profile can extend) is held in an Enum column
   (an array of the Enum for a 0..* element, a column on the index row for an element inside a
   repeating backbone element). A `code` with an extensible / preferred / example binding, and every
   CodeableConcept / Coding, is never an enum: a profile may add codes, so those live in the token
   tables as strings.

When a new resource is rebuilt, `test_required_code_parameters_are_held_in_enums` fails until its
required-binding codes are listed in REQUIRED_CODE_STORAGE below - on purpose: it is the checklist
item that was missed once for AllergyIntolerance.category / reaction.severity and
Appointment.participant.status.
"""

import json
import os
import re
import tarfile
from functools import cache

import pytest
import sqlalchemy as sa

r4_package = pytest.importorskip(
    "google.fhir.r4.r4_package", reason="google-fhir-r4 is a dev-only dependency"
)

import app.main  # noqa: E402,F401 - imports every model and registry
from app.core.database import FHIRBase  # noqa: E402
from app.fhir.capability import SEARCH_REGISTRIES  # noqa: E402

STRENGTH = {1: "required", 2: "extensible", 3: "preferred", 4: "example"}

# (resource, search parameter) -> (table, column): where a required-binding `code` is held.
REQUIRED_CODE_STORAGE = {
    ("AllergyIntolerance", "category"): ("allergy_intolerance", "category"),
    ("AllergyIntolerance", "criticality"): ("allergy_intolerance", "criticality"),
    ("AllergyIntolerance", "severity"): ("allergy_intolerance_reaction", "severity"),
    ("AllergyIntolerance", "type"): ("allergy_intolerance", "type"),
    ("Appointment", "part-status"): ("appointment_participant", "status"),
    ("Appointment", "status"): ("appointment", "status"),
    ("AppointmentResponse", "part-status"): (
        "appointment_response",
        "participant_status",
    ),
    ("CarePlan", "intent"): ("care_plan", "intent"),
    ("CarePlan", "status"): ("care_plan", "status"),
    ("CareTeam", "status"): ("care_team", "status"),
    ("ClinicalImpression", "status"): ("clinical_impression", "status"),
    ("DiagnosticReport", "status"): ("diagnostic_report", "status"),
    ("Encounter", "status"): ("encounter", "status"),
    ("DocumentReference", "relation"): ("document_reference_relates_to", "code"),
    ("DocumentReference", "status"): ("document_reference", "status"),
    ("Endpoint", "status"): ("endpoint", "status"),
    ("EpisodeOfCare", "status"): ("episode_of_care", "status"),
    ("FamilyMemberHistory", "status"): ("family_member_history", "status"),
    ("Goal", "lifecycle-status"): ("goal", "lifecycle_status"),
    ("Group", "type"): ("group", "type"),
    ("Immunization", "status"): ("immunization", "status"),
    ("ImmunizationEvaluation", "status"): ("immunization_evaluation", "status"),
    ("Location", "address-use"): ("location", "address_use"),
    ("Location", "status"): ("location", "status"),
    ("Medication", "status"): ("medication", "status"),
    ("MedicationAdministration", "status"): ("medication_administration", "status"),
    ("MedicationDispense", "status"): ("medication_dispense", "status"),
    ("MedicationKnowledge", "status"): ("medication_knowledge", "status"),
    ("MedicationRequest", "intent"): ("medication_request", "intent"),
    ("MedicationRequest", "priority"): ("medication_request", "priority"),
    ("MedicationRequest", "status"): ("medication_request", "status"),
    ("MedicationStatement", "status"): ("medication_statement", "status"),
    ("Observation", "status"): ("observation", "status"),
    ("Organization", "address-use"): ("organization_address", "use"),
    ("Patient", "address-use"): ("patient_address", "use"),
    ("Patient", "gender"): ("patient", "gender"),
    ("Practitioner", "address-use"): ("practitioner_address", "use"),
    ("Practitioner", "gender"): ("practitioner", "gender"),
    ("Procedure", "status"): ("procedure", "status"),
    ("Questionnaire", "status"): ("questionnaire", "status"),
    ("Questionnaire", "subject-type"): ("questionnaire", "subject_type"),
    ("QuestionnaireResponse", "status"): ("questionnaire_response", "status"),
    ("RelatedPerson", "address-use"): ("related_person_address", "use"),
    ("RelatedPerson", "gender"): ("related_person", "gender"),
    ("ServiceRequest", "intent"): ("service_request", "intent"),
    ("ServiceRequest", "priority"): ("service_request", "priority"),
    ("ServiceRequest", "status"): ("service_request", "status"),
    ("Slot", "status"): ("slot", "status"),
    ("Specimen", "status"): ("specimen", "status"),
}


# Search parameters that read a `code` with a *required* binding whose value set is open-ended (not
# a list HL7 can enumerate), so they cannot be enums: they stay strings.
#   DocumentReference.contenttype -> Attachment.contentType, bound (required) to the mime-type value
#   set, which is every BCP 13 media type.
OPEN_REQUIRED_BINDINGS = {("DocumentReference", "contenttype")}


@cache
def _package():
    return r4_package.load_base_r4()


@cache
def _hl7_search_parameters() -> dict[str, dict[str, tuple[str, str]]]:
    """resource -> {search parameter code: (type, expression)} from the raw HL7 JSON."""
    path = os.path.join(
        os.path.dirname(r4_package.__file__), "data", "hl7.fhir.r4.core.tgz"
    )
    out: dict[str, dict[str, tuple[str, str]]] = {}
    with tarfile.open(path) as tar:
        for member in tar.getmembers():
            name = os.path.basename(member.name)
            if name.startswith("SearchParameter-") and name.endswith(".json"):
                sp = json.load(tar.extractfile(member))
                for base in sp.get("base", []):
                    out.setdefault(base, {})[sp["code"]] = (
                        sp["type"],
                        sp.get("expression", ""),
                    )
    return out


@cache
def _elements(resource_type: str) -> dict[str, dict]:
    sd = _package().get_structure_definition(
        f"http://hl7.org/fhir/StructureDefinition/{resource_type}"
    )
    out = {}
    for el in sd.snapshot.element:
        has_binding = el.HasField("binding")
        out[el.id.value] = {
            "types": [t.code.value for t in el.type],
            "strength": STRENGTH.get(el.binding.strength.value)
            if has_binding
            else None,
        }
    return out


def _element(resource_type: str, element_id: str) -> dict | None:
    """The element, looked up in the resource or - for `Patient.address.use` - in its datatype."""
    found = _elements(resource_type).get(element_id) or _elements(resource_type).get(
        element_id + "[x]"
    )
    if found:
        return found
    segments = element_id.split(".")
    for cut in range(len(segments) - 1, 0, -1):
        parent = _elements(resource_type).get(".".join(segments[:cut]))
        if parent and len(parent["types"]) == 1:
            datatype = parent["types"][0]
            if datatype[0].isupper() and datatype not in ("BackboneElement", "Element"):
                rest = ".".join(segments[cut:])
                return _elements(datatype).get(f"{datatype}.{rest}")
    return None


def _element_ids(expression: str, resource_type: str) -> list[str]:
    ids = []
    for alternative in re.split(r"\s*\|\s*", expression):
        alternative = alternative.strip().strip("()")
        alternative = re.sub(r"\s+as\s+.*$", "", alternative)
        alternative = (
            re.split(
                r"\.(?:where|as|ofType|exists|first|resolve|extension)\b", alternative
            )[0]
            .replace("(", "")
            .replace(")", "")
        )
        if alternative.startswith(resource_type + "."):
            ids.append(alternative)
    return ids


def _required_code_parameters(resource_type: str) -> set[str]:
    needed = set()
    for code, (stype, expression) in (
        _hl7_search_parameters().get(resource_type, {}).items()
    ):
        if code.startswith("_") or stype != "token" or "xtension(" in expression:
            continue
        for element_id in _element_ids(expression, resource_type):
            element = _element(resource_type, element_id)
            if (
                element
                and "code" in element["types"]
                and element["strength"] == "required"
                and (resource_type, code) not in OPEN_REQUIRED_BINDINGS
            ):
                needed.add(code)
    return needed


def _registries():
    return {
        factory().resource_type: factory() for factory in SEARCH_REGISTRIES.values()
    }


@pytest.mark.parametrize("resource_type", sorted(_registries()))
def test_search_parameters_match_the_hl7_resource_page(resource_type):
    ours = {n for n in _registries()[resource_type].params if not n.startswith("_")}
    theirs = {
        code
        for code, (_type, expression) in _hl7_search_parameters()
        .get(resource_type, {})
        .items()
        if not code.startswith("_") and expression and "xtension(" not in expression
    }
    assert ours == theirs, (
        f"{resource_type}: missing {sorted(theirs - ours)}, not in R4 {sorted(ours - theirs)}"
    )
    for code, (stype, _expr) in _hl7_search_parameters()[resource_type].items():
        if code in ours:
            assert _registries()[resource_type].params[code].type == stype, (
                f"{resource_type}.{code} is a {stype} search parameter in R4"
            )


@pytest.mark.parametrize("resource_type", sorted(_registries()))
def test_required_code_parameters_are_held_in_enums(resource_type):
    needed = _required_code_parameters(resource_type)
    declared = {p for (r, p) in REQUIRED_CODE_STORAGE if r == resource_type}
    assert needed == declared, (
        f"{resource_type}: required-binding `code` search parameters {sorted(needed)} but "
        f"REQUIRED_CODE_STORAGE lists {sorted(declared)} - hold each in a Postgres enum column "
        "(ARRAY of the enum for a 0..* element) and list it here"
    )
    for param in declared:
        table, column = REQUIRED_CODE_STORAGE[(resource_type, param)]
        col_type = FHIRBase.metadata.tables[table].c[column].type
        item = col_type.item_type if isinstance(col_type, sa.ARRAY) else col_type
        assert isinstance(item, sa.Enum), (
            f"{resource_type}.{param}: {table}.{column} must be a Postgres enum, not {col_type!r}"
        )
