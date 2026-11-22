from enum import Enum


class AllergyIntoleranceType(str, Enum):
    allergy = "allergy"
    intolerance = "intolerance"


class AllergyIntoleranceCategory(str, Enum):
    """AllergyIntolerance.category (0..*, required binding allergy-intolerance-category)."""

    food = "food"
    medication = "medication"
    environment = "environment"
    biologic = "biologic"


class AllergyIntoleranceReactionSeverity(str, Enum):
    """AllergyIntolerance.reaction.severity (0..1, required binding reaction-event-severity)."""

    mild = "mild"
    moderate = "moderate"
    severe = "severe"


class AllergyIntoleranceCriticality(str, Enum):
    """AllergyIntoleranceCriticality — stored by value, so `unable-to-assess`
    is the real FHIR code."""

    low = "low"
    high = "high"
    unable_to_assess = "unable-to-assess"
