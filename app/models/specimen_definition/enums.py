from enum import Enum


class SpecimenDefinitionPreference(str, Enum):
    """Specimen preference: preferred | alternate."""

    preferred = "preferred"
    alternate = "alternate"


class SpecimenDefinitionQuantityComparator(str, Enum):
    """Quantity comparator: lt | le | ge | gt (mapped to < | <= | >= | > in schemas/mappers)."""

    lt = "lt"
    le = "le"
    ge = "ge"
    gt = "gt"


class SpecimenDefinitionAdditiveReferenceType(str, Enum):
    """FHIR R4 target types for SpecimenDefinition.typeTested.container.additive.additiveReference."""

    Substance = "Substance"
