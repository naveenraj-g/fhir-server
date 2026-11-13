from app.core.config import settings
from app.core.logging import get_logger
from app.errors.auth import PermissionDeniedError
from app.errors.domain import NotFoundError
from app.errors.validation import FhirValidationError
from app.fhir.datatypes import merge_patch_fragment
from app.fhir.input_payload import fhir_create_document, fhir_patch_fragment
from app.fhir.mappers.organization import to_fhir_organization
from app.fhir.search import SearchContext, SearchRequest, parse_search
from app.fhir.validation import validate_resource
from app.models.organization import OrganizationModel
from app.repository.organization import OrganizationRepository
from app.repository.organization.search import organization_search
from app.schemas.organization import OrganizationCreateSchema, OrganizationPatchSchema

logger = get_logger(__name__)


class _CoreMixin:
    """All Organization business logic. Unlike Patient/Practitioner,
    Organization has no standalone sub-resource endpoints and no separate
    scalar-only vs. full create/patch split — see OrganizationCreateSchema's
    docstring. Auth is otherwise identical to Patient/Practitioner: org_id
    comes from the verified JWT's activeOrganizationId claim (actor.org_id),
    never a client-suppliable field, and there's no org-less/super-admin
    bypass — every operation requires an org-scoped actor."""

    def __init__(self, repository: OrganizationRepository):
        self.repository = repository

    # ── Formatters ────────────────────────────────────────────────────────

    def _to_fhir(self, org: OrganizationModel) -> dict:
        return to_fhir_organization(org)

    # ── Read ──────────────────────────────────────────────────────────────

    async def get_organization_scoped(
        self, organization_id: int, org_id: str | None
    ) -> OrganizationModel:
        """Requires an org-scoped actor — raises PermissionDeniedError (403)
        for an org-less token instead of silently falling back to an
        unscoped lookup, then NotFoundError (404, never 403) if it belongs
        to a different org, so existence isn't leaked."""
        if not org_id:
            raise PermissionDeniedError(
                "Organization operation requires an org-scoped token"
            )
        org = await self.repository.get_by_organization_id_in_org(
            organization_id, org_id
        )
        if not org:
            raise NotFoundError("Organization not found")
        return org

    async def search_organizations(
        self,
        query: list[tuple[str, str]],
        org_id: str | None,
        *,
        strict: bool = False,
        fhir_base: str | None = None,
    ) -> tuple[
        SearchRequest, list[OrganizationModel], int | None, list[OrganizationModel]
    ]:
        """FHIR R4 search. `query` is the raw (key, value) parameter list
        — parsed and validated here against the Organization search
        registry (SearchError -> 400 OperationOutcome). `strict` is
        `Prefer: handling=strict`. Raises PermissionDeniedError (403) for an
        org-less token — same invariant as get_organization_scoped().

        Returns (parsed request, matches, total, included (type, row) —
        an include can be another resource type, e.g. Location)."""
        if not org_id:
            raise PermissionDeniedError(
                "Organization operation requires an org-scoped token"
            )
        request = parse_search(
            query,
            organization_search(),
            strict=strict,
            default_count=settings.pagination.default_limit,
            max_count=settings.pagination.max_limit,
        )
        ctx = SearchContext(tenant_id=org_id, fhir_base=fhir_base)
        rows, total, included = await self.repository.search(request, ctx)
        return request, rows, total, included

    # ── Write ─────────────────────────────────────────────────────────────

    async def create_organization(
        self,
        payload: OrganizationCreateSchema,
        org_id: str | None,
        created_by: str | None,
        body: dict | None = None,
    ) -> OrganizationModel:
        """org_id comes from the verified JWT's actor.org_id, not a client-
        supplied field — there is no bypass, so an org-less/platform token
        cannot create an Organization at all.

        `body` is the raw request JSON, which is what base R4 validation
        checks (see app.fhir.input_payload); falls back to the parsed
        payload for internal callers that have no raw body."""
        if not org_id:
            raise PermissionDeniedError(
                "Organization creation requires an org-scoped token"
            )
        # The body is already a FHIR Organization — validate it as sent,
        # then store exactly that document.
        document = fhir_create_document(self._raw(payload, body), "Organization")
        await self._validate_base_r4(document, org_id)
        org = await self.repository.create_full(document, org_id, created_by)
        logger.info(
            "Organization created",
            extra={
                "event": "organization.created",
                "organization_id": org.organization_id,
            },
        )
        return org

    async def patch_organization(
        self,
        organization_id: int,
        payload: OrganizationPatchSchema,
        updated_by: str | None = None,
        org_id: str | None = None,
        body: dict | None = None,
    ) -> OrganizationModel:
        """org_id comes from the verified JWT's actor.org_id — no bypass: a
        missing org_id or an organization belonging to a different org both
        raise NotFoundError (404), never 403, so existence isn't leaked.

        The current row is fetched (rather than a lightweight existence
        check) because base R4 validation needs it: a PATCH payload is
        partial by nature, so it's merged onto the resource's current full
        FHIR representation before validating — see
        app.fhir.input_payload.fhir_patch_fragment()."""
        if not org_id:
            self._log_org_scope_miss("patch", organization_id, org_id)
            raise NotFoundError("Organization not found")
        existing = await self.repository.get_by_organization_id_in_org(
            organization_id, org_id
        )
        if not existing:
            self._log_org_scope_miss("patch", organization_id, org_id)
            raise NotFoundError("Organization not found")

        fragment, touched = fhir_patch_fragment(self._raw(payload, body))
        merged = merge_patch_fragment(to_fhir_organization(existing), fragment, touched)
        await self._validate_base_r4(merged, org_id)

        # `merged` — the resource as it will look after this patch — is what
        # was just validated, and exactly what gets stored.
        updated = await self.repository.patch_full(organization_id, merged, updated_by)
        if not updated:
            raise NotFoundError("Organization not found")
        logger.info(
            "Organization updated",
            extra={
                "event": "organization.updated",
                "organization_id": organization_id,
                "fields": sorted(touched),
            },
        )
        return updated

    async def delete_organization(
        self, organization_id: int, org_id: str | None = None
    ) -> None:
        """Same org_id ownership gate as patch_organization."""
        if not org_id or not await self.repository.organization_belongs_to_org(
            organization_id, org_id
        ):
            self._log_org_scope_miss("delete", organization_id, org_id)
            raise NotFoundError("Organization not found")
        deleted = await self.repository.delete(organization_id)
        if not deleted:
            raise NotFoundError("Organization not found")
        logger.info(
            "Organization deleted",
            extra={
                "event": "organization.deleted",
                "organization_id": organization_id,
            },
        )

    # ── Validation helpers ────────────────────────────────────────────────

    @staticmethod
    def _raw(payload, body: dict | None) -> dict:
        """The client's request JSON as sent; when there isn't one (an
        internal caller), the parsed payload's supplied fields instead."""
        if body is not None:
            return body
        return payload.model_dump(mode="json", exclude_unset=True)

    @staticmethod
    async def _validate_base_r4(fhir_resource: dict, org_id: str | None = None) -> None:
        """Raises FhirValidationError (422) if `fhir_resource` fails
        validation against the most specific applicable layer of the
        base -> country -> organization profile chain (see
        docs/architecture/fhir-profiling-and-extensibility-strategy.md).
        Delegates to validate_resource(), which picks the actual backend
        (this project's own structural-only check, or the HL7 Java validator
        sidecar — which also enforces real invariants) per
        settings.fhir_validation.backend, and — for java_validator — the
        most specific of org/country/base that has a row, passing `org_id`
        through so the organization layer is considered — see
        docs/structure-definitions/12-three-layer-validation-architecture.md.
        No organization-scope profile row exists in the DB yet (no admin
        write path for that layer), so this always falls through to
        country/base today — see validate_resource()'s own docstring."""
        errors = await validate_resource("Organization", fhir_resource, org_id=org_id)
        if errors:
            logger.warning(
                "Organization failed base R4 validation",
                extra={"event": "organization.base_r4_invalid", "errors": errors},
            )
            raise FhirValidationError(errors)

    # ── Logging helpers ───────────────────────────────────────────────────

    @staticmethod
    def _log_org_scope_miss(
        operation: str, organization_id: int, org_id: str | None
    ) -> None:
        """The tenant gate rejected a write. The caller gets a plain 404 —
        deliberately indistinguishable from "no such organization" — so this
        log line is the only place the distinction is recorded. Worth WARNING
        because a repeated cross-org miss is a very different signal from a
        typo'd id."""
        logger.warning(
            "Organization write rejected by org scope",
            extra={
                "event": "organization.org_scope_miss",
                "operation": operation,
                "organization_id": organization_id,
                "reason": "no_org_token" if not org_id else "different_org",
            },
        )
