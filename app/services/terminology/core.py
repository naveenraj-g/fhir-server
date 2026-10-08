from app.repository.terminology import TerminologyRepository


class _CoreMixin:
    """Just the constructor — terminology has no single primary resource
    row the way Patient/Organization have one, so there's no "core"
    business logic to host here, only the shared __init__ every mixin in
    this package needs."""

    def __init__(self, repository: TerminologyRepository):
        self.repository = repository
