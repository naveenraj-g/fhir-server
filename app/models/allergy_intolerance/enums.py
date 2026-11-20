from enum import Enum


class AllergyIntoleranceType(str, Enum):
    allergy = "allergy"
    intolerance = "intolerance"


class AllergyIntoleranceCriticality(str, Enum):
    """AllergyIntoleranceCriticality — stored by value, so `unable-to-assess`
    is the real FHIR code."""

    low = "low"
    high = "high"
    unable_to_assess = "unable-to-assess"
