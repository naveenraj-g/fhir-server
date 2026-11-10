"""FHIR R4 ConceptMap.group.element.target.equivalence — verbatim from
https://www.hl7.org/fhir/R4/valueset-concept-map-equivalence.html, a
required binding (ConceptMap.group.element.target.equivalence is 1..1).
Read as: how the TARGET relates to the SOURCE. See
docs/terminology-service/09-fhir-r4-terminology-standard-reference.md §4.2
for the verbatim HL7 definition text behind each member.

This replaces TerminologyConceptMap's former free-text `mapping_type`
string column — see docs/terminology-service/08-fhir-r4-standard-compliance-gap-analysis.md
§4 for why a free string was the gap this closes."""

from enum import Enum


class ConceptMapEquivalence(str, Enum):
    relatedto = "relatedto"
    equivalent = "equivalent"
    equal = "equal"
    wider = "wider"
    subsumes = "subsumes"
    narrower = "narrower"
    specializes = "specializes"
    inexact = "inexact"
    unmatched = "unmatched"
    disjoint = "disjoint"
