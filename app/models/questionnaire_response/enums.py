from enum import Enum


class QuestionnaireResponseStatus(str, Enum):
    """QuestionnaireResponse.status (questionnaire-answers-status, required) - stored by value, so
    the real FHIR codes `in-progress` and `entered-in-error` are what the database holds."""

    in_progress = "in-progress"
    completed = "completed"
    amended = "amended"
    entered_in_error = "entered-in-error"
    stopped = "stopped"
