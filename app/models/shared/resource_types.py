"""The R4 resource type names, for `Reference(Any)` search parameters.

A `Reference(Any)` element (DetectedIssue.implicated, Observation.focus, ...) may name any
resource type, so its `SearchParam.targets` is this whole list - the spec's own, not a
hand-typed guess. A plain reference search (`implicated=Foo/5`) then accepts any valid R4 type
and rejects a made-up one; chaining and `_include` are limited to the types that are rebuilt on
this server (`SearchParam.chain_targets`), whatever the list says.
"""

from app.models.questionnaire.enums import QuestionnaireSubjectType

# HL7's closed `resource-types` code system (148 types in R4), already held as an enum for
# Questionnaire.subjectType.
ANY_RESOURCE_TYPES: tuple[str, ...] = tuple(t.value for t in QuestionnaireSubjectType)


def is_any(targets: tuple[str, ...]) -> bool:
    """True for the target list of a Reference(Any) parameter."""
    return targets is ANY_RESOURCE_TYPES
