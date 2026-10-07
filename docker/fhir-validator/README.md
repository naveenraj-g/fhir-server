# FHIR Validator sidecar

A Docker build of [`inferno-framework/fhir-validator-wrapper`](https://github.com/inferno-framework/fhir-validator-wrapper)
(pinned to `v2.3.6`) — a REST wrapper around the official HL7 Java FHIR validator.

## Why this exists

A stopgap for structural/profile/invariant validation against real `StructureDefinition`
documents — base R4, and eventually this project's own country/organization profile layers —
until this project's own validation engine is built. See
[`docs/architecture/fhir-profiling-and-extensibility-strategy.md`](../../docs/architecture/fhir-profiling-and-extensibility-strategy.md)
and
[`docs/structure-definitions/12-three-layer-validation-architecture.md`](../../docs/structure-definitions/12-three-layer-validation-architecture.md).

The intended usage pattern: this project's own `fhir_profile` DB table (design: that
architecture document's §3) stays the single source of truth for every profile layer. A thin
Python client converts a resolved profile row into true `StructureDefinition` JSON and `POST`s
it to this container's `/profiles` endpoint; validating an instance means `POST /validate?profile=<url>`.
When the project's own engine is ready, only that thin client gets replaced — the DB table and
the StructureDefinition-shaped data it holds don't change.

## Running it

Via the dev compose stack (recommended for local work):

```
docker compose -f docker-compose.dev.yml up -d fhir-validator
```

Or standalone:

```
docker build -t fhir-validator-wrapper docker/fhir-validator
docker run -p 4567:4567 fhir-validator-wrapper
```

Confirm it's up:

```
curl http://localhost:4567/version
```

## Key endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/version` | Wrapper + validator version — use this to confirm the container is ready. |
| `POST` | `/profiles` | Register a `StructureDefinition` (JSON body) — base/country/org layer. |
| `GET` | `/profiles` | List every registered profile URL. |
| `POST` | `/validate?profile=<url>` | Validate a resource (JSON body) against a registered profile. |
| `POST` | `/evaluate?path=<FHIRPath>` | Evaluate a FHIRPath expression against a resource (JSON body) — usable for `org-1`/`org-2`/`org-3` and any custom invariant. |

Full reference: [upstream `rest-api.md`](https://github.com/inferno-framework/fhir-validator-wrapper/blob/main/rest-api.md).

## Open item

Whether `POST /profiles` registrations survive a container restart (they're almost certainly
held in the running JVM's in-memory validator context, not persisted to disk) hasn't been
confirmed yet — assume they don't, and re-register from this project's `fhir_profile` table on
every container startup once that wiring exists.
