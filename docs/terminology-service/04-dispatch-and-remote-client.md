# Dispatch and the Remote Client

**What this file is:** everything else in this server that needs to check
a code, look up a concept, or translate between code systems (see
[00-what-is-terminology.md](00-what-is-terminology.md) if those words are
new) does so through one shared interface, without caring whether the
actual terminology data lives in this same process or in a separate
service reached over the network. This file explains how that choice is
made and swapped.

The terminology service is the one subsystem in this codebase explicitly
designed to run either in-process or as a separate HTTP service, decided by
one config flag. This file covers the three pieces that make that swap
possible without the caller ever knowing which backend it's talking to.

## `app/terminology/client.py` — the `TerminologyClient` Protocol (124 lines)

A `typing.Protocol` (structural typing — no explicit `class X(TerminologyClient)`
inheritance required anywhere) declaring the full 17-method contract both
implementations below satisfy: code-system/value-set listing and lookup,
concept search/lookup, `validate()`/`translate()`, concept-map list/add, and
the full org-concept + display-override CRUD surface. Because it's
structural, `TerminologyService` (the embedded implementation) satisfies it
automatically just by having matching method signatures — it doesn't
`import` or reference `TerminologyClient` at all.

## `app/terminology/dispatch.py` (31 lines)

```python
def get_terminology_client(embedded_service: TerminologyClient) -> TerminologyClient:
```

Reads `settings.terminology.backend` (`"embedded"` or `"remote"`,
`TerminologyConfig` in `app/core/config.py`). `"embedded"` (the default)
returns `embedded_service` unchanged. `"remote"` constructs and returns a
`RemoteTerminologyClient(base_url=settings.terminology.remote.base_url,
timeout_seconds=settings.terminology.remote.timeout_seconds)` instead. The
caller — anything that depends on `get_terminology_client()` via DI, see
below — always gets back something satisfying `TerminologyClient`, and never
branches on which one it got.

## `app/terminology/remote_client.py` (324 lines)

`RemoteTerminologyClient.__init__(base_url, timeout_seconds=30.0)`.
`_client()` builds an `httpx.AsyncClient` with `base_url=<base_url>/api/v1/terminology`
and the configured timeout. Each of the 17 `TerminologyClient` methods makes
exactly one HTTP call against this server's own terminology routes (see
[03-api-routes.md](03-api-routes.md)) and `model_validate()`s the JSON
response straight into the matching `app/schemas/terminology.py` response
class — i.e. it's calling *this same codebase's* terminology API, just over
the network instead of in-process, which is exactly the shape you'd want if
multiple FHIR-server instances each ran with `backend: remote` pointed at
one shared terminology instance.

**Auth is an explicitly unsolved placeholder here.** The org-scoped methods
(create/patch/delete on org-concepts and display-overrides) forward
`X-Org-Id`/`X-User-Id` headers on the outgoing request. The module's own
docstring flags this directly: the *receiving* router doesn't read those
headers at all — it authenticates via `request.state.user`, populated by
whatever's upstream of it (see `_require_org_id()` in
[03-api-routes.md](03-api-routes.md)). So today, a `RemoteTerminologyClient`
call to an org-scoped write endpoint depends on the receiving terminology
instance's own upstream auth already being satisfied some other way — the
`X-Org-Id`/`X-User-Id` headers this client sends are not currently consumed
by anything on the other end. Don't treat their presence as "auth is
handled"; it isn't, yet.

## DI wiring

- `app/di/modules/terminology.py` (19 lines) — `TerminologyContainer` with
  `terminology_repository` and `terminology_service` as `Factory` providers
  (repository takes the session factory, service takes the repository —
  standard DI-container boilerplate per the root `CLAUDE.md`'s "Dependency
  Injection" section).
- `app/di/dependencies/terminology.py` (22 lines) — the `@inject`-wrapped
  `get_terminology_client` FastAPI dependency. It resolves the embedded
  `TerminologyService` via `Provide[Container.terminology.terminology_service]`,
  then passes it through `dispatch.py`'s `get_terminology_client()` — so the
  actual backend-selection logic lives in exactly one place
  (`dispatch.py`), and the DI dependency is just the FastAPI-facing wrapper
  around it.

## Config

`app/core/config.py` lines ~178–212:

```python
class TerminologyRemoteConfig(BaseModel):
    base_url: str = "http://localhost:8000"
    timeout_seconds: float = 30.0

class TerminologyConfig(BaseModel):
    backend: Literal["embedded", "remote"] = "embedded"
    remote: TerminologyRemoteConfig = TerminologyRemoteConfig()
```

Like every other nested settings field, `terminology.backend` can be
overridden via env var without touching `configs/config.yaml`, using the
`__` nesting delimiter the root `CLAUDE.md` describes —
`TERMINOLOGY__BACKEND=remote`.
