# Load routes, dependencies, and DI wiring in the FastAPI `lifespan` handler — txtai's `application.py` pattern

## Context

Naveen pointed at `txtai`'s `src/python/txtai/api/application.py` as the reference for how routes and dependencies should be loaded, and wants fhir-server's `app/main.py` restructured to match it: **routers get discovered and mounted, and DI gets wired, inside the FastAPI `lifespan` async context manager — at actual ASGI startup — not at module-import time**, the way `app/main.py` does it today (and the way the now-reverted config/DI work from earlier this session also did it — that work built the right *data* (`configs/routes.yaml`'s enabled set, a DI module registry) but still wired everything at import time, one level short of what txtai actually does).

Config loading itself is **not** part of what's being copied — txtai reads a single YAML path off `os.environ["CONFIG"]` (`Application.read(...)`); fhir-server keeps its own `Settings` (pydantic-settings, `.env` + `configs/config.yaml`, per the layered system this session already built) as the config source. Only the *discovery-and-mounting-at-lifespan-startup* mechanism is being adopted, re-pointed at our own config.

## What txtai actually does (read directly from the source)

`txtai/api/application.py`:
```python
def apirouters():
    """Lists available APIRouters by introspecting the api package's own
    namespace for submodules exposing a `router: APIRouter` attribute."""
    api = sys.modules[".".join(__name__.split(".")[:-1])]  # the txtai.api package
    available = {}
    for name, rclass in inspect.getmembers(api, inspect.ismodule):
        if hasattr(rclass, "router") and isinstance(rclass.router, APIRouter):
            available[name.lower()] = rclass.router
    return available


def lifespan(application):
    global INSTANCE
    config = Application.read(os.environ.get("CONFIG"))          # config loaded at startup, not import
    INSTANCE = APIFactory.create(config, api) if api else API(config)  # heavy object built at startup

    routers = apirouters()                                        # routers discovered via introspection
    for name, router in routers.items():
        if name in config and enabled(config, name):              # two-part gate, see below
            application.include_router(router)                    # mounted at startup, not import
    ...
    yield                                                          # startup ends here; shutdown code after


app, INSTANCE = FastAPI(lifespan=lifespan), None                   # app object created immediately; body runs later
```

Two mechanisms, worth separating:

1. **Introspection-based discovery** (`apirouters()`) — no hand-written registry. `txtai/api/routers/__init__.py` does `from . import embeddings`, `from . import agent`, etc. (binding each **submodule object**, not an attribute pulled out of it), and `txtai/api/__init__.py` does `from .routers import *`, which — because `routers/__init__.py` has no `__all__` — re-exports every one of those submodule names onto the `txtai.api` package's own namespace. `apirouters()` then walks that namespace with `inspect.getmembers(api, inspect.ismodule)` and picks out every submodule that happens to expose a module-level `router: APIRouter`. Adding a new route module is just adding one `from . import <name>` line — no second place to register it.

2. **Lifespan-time mounting** — `application.include_router(...)` calls happen inside the `lifespan` async generator, before `yield`. FastAPI/ASGI runs this at actual server startup (Uvicorn's `startup` lifecycle event), not when `app/main.py` is imported. The enable check itself (`enabled()`) is a two-part gate: `name in config` (the resource's own top-level config section must exist at all — e.g. an `embeddings:` block) **and** `enabled(config, name)` (`config.get("routes", {}).get(name, True)` — defaults to enabled unless explicitly set `false`). The first half doesn't have a direct analog in fhir-server today (there's no per-resource top-level config section, only the flat `configs/routes.yaml` enabled-list) — not adopting it now; flagged as a natural extension if plan `02-settings-domain-split.md`'s per-domain config sections ever grow to cover individual resources.

## The one incompatibility that has to be resolved first

fhir-server's `app/routers/__init__.py` imports router modules like this today:
```python
from .patient import router as patient_router
```
— it extracts the `router` attribute immediately and binds it to a new name (`patient_router`), never binding the **submodule itself** anywhere. txtai's introspection needs the submodule object bound in the package namespace (`from . import patient`) so it can later ask "does this module have a `.router` attribute." **This import style has to change** before introspection-based discovery is possible — not a config change, a structural one:
```python
from . import patient, practitioner, organization, encounter, ...  # bind submodules, not extracted routers
```
Same change applies to `app/di/modules/__init__.py` for the DI equivalent (see below).

## Changes

### 1. `app/routers/__init__.py` — replace `_ROUTERS` with introspection
- Change every `from .<name> import router as <name>_router` to `from . import <name>` (bind the submodule).
- Add a `discover_routers()` function, mirroring `apirouters()` exactly:
  ```python
  def discover_routers() -> dict[str, APIRouter]:
      """Introspects this package's own namespace for submodules exposing a
      module-level `router: APIRouter` — mirrors txtai's api/application.py
      apirouters(). Adding a new resource means adding one `from . import
      <name>` line above — nothing else to register."""
      here = sys.modules[__name__]
      return {
          name: mod.router
          for name, mod in inspect.getmembers(here, inspect.ismodule)
          if isinstance(getattr(mod, "router", None), APIRouter)
      }
  ```
- **Confirmed against the real code** (`app/routers/patient/__init__.py`): every resource does `router = APIRouter()` with no `prefix=`/`tags=` at construction — those are only attached externally, via `_ROUTERS`' `(router, prefix, tag)` tuples, at `include_router()` time. txtai's `application.include_router(router)` takes no prefix argument at all, which only works because txtai's route modules bake their own path into each `@router.get(...)`/`@router.post(...)` decorator directly (no shared resource-level prefix). Two ways to reconcile this with fhir-server's prefix-per-resource convention (`/patients`, `/organizations`, etc.):
  - **(a)** Move `prefix=`/`tags=` into each `app/routers/<resource>/__init__.py`'s `APIRouter(prefix="/patients", tags=["Patients"])` constructor call — one mechanical edit across all ~34 router packages — so `discover_routers()` can return bare `APIRouter` objects ready to `include_router(router)` with zero extra bookkeeping, matching txtai exactly.
  - **(b)** Keep prefix/tag in a small parallel `dict[str, tuple[str, str]]` (name → (prefix, tag)) alongside the introspected router dict — less mechanical churn, but doesn't fully eliminate a hand-maintained table the way txtai's version does.
  - **Recommendation: (a)** — it's the more faithful port of the actual pattern being asked for, the diff is uniform and mechanical (same one-line constructor change repeated ~34 times), and it removes prefix/tag bookkeeping from `app/routers/__init__.py` entirely rather than just relocating it.

### 2. `app/di/modules/__init__.py` — same treatment for DI
- Replace the hand-written `DI_MODULES` dict (from the now-reverted work) with the same introspection idea: each `app/di/modules/<resource>.py` module exposes its `<Resource>Container` class at a predictable attribute name (or a conventional `container = <Resource>Container` alias), and a `discover_di_modules()` walks the package namespace the same way `discover_routers()` does.

### 3. `app/main.py` — move mounting into `lifespan`
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🟢 Starting up the application")

    # Build + wire the DI container at startup, not import time.
    container = build_container()          # from app.di.container — no config-driven filtering needed
    app.container = container              # if anything still needs app.container post-startup
    db: Database = container.core.database()
    await db.create_extensions()

    # Discover + conditionally mount routers at startup.
    enabled = load_enabled_routes(settings.ROUTES_CONFIG_PATH)
    for name, router in discover_routers().items():
        if name in enabled:
            app.include_router(router, prefix="/api/fhir/v1", dependencies=[Depends(get_current_user)])

    try:
        await cast(Any, redis_client.ping())
        app.state.redis = redis_client
    except Exception as e:
        logger.error("Failed to connect to Redis.", exc_info=e)
        app.state.redis = None

    yield

    logger.info("🔴 Shutting down application...")
    await db.disconnect()
```
`app = FastAPI(lifespan=lifespan, ...)` is constructed immediately at module level (cheap — just the FastAPI object, no routes yet); everything expensive/config-dependent moves into the function body above, executed once by Uvicorn's ASGI `startup` event.

### 4. The DI circular-import fragility (flagged in the earlier, now-reverted plan) disappears for free
Building `Container` inside `lifespan()` means `Container` is a **local variable**, resolved after `app/main.py` has already fully finished importing (lifespan runs long after import time) — there's no scenario where `Container.wire(packages=["app"])`'s package walk can re-trigger a partial import of `app.di.container`, because by the time lifespan fires, every module is already fully imported. This is a genuine simplification over the previous (reverted) approach, not just a stylistic change.

## The blocking risk this plan must resolve: `tests/conftest.py`

```python
async with AsyncClient(transport=ASGITransport(app=app), ...) as client:
```
`httpx.ASGITransport` does **not** run the ASGI lifespan protocol on its own — confirmed by grepping `tests/conftest.py` for `lifespan`/`LifespanManager`: no matches. Today this doesn't matter because every route is mounted and DI is wired at import time, before the test client ever touches `app`. The moment mounting moves into `lifespan`, every integration test would see a FastAPI app with **zero routes and no DI wiring** unless the lifespan startup is explicitly triggered per test session.

**Required companion fix** — wrap the test app in a lifespan-aware context manager, e.g. using the `asgi-lifespan` package (`uv add --group dev asgi-lifespan`):
```python
from asgi_lifespan import LifespanManager

@pytest.fixture(scope="session")
async def _app_lifespan():
    async with LifespanManager(app):
        yield
```
and have the existing `AsyncClient(transport=ASGITransport(app=app))` fixtures depend on `_app_lifespan` so startup runs exactly once per test session before any request fires. This is not optional polish — without it, this plan breaks every integration test in the suite.

## Verification

- `uv run python -c "import app.main; print('OK')"` — must still succeed, and must be *fast*/side-effect-free (no DB/router work should happen at import time anymore — only at actual startup).
- Update `tests/conftest.py` per the `asgi-lifespan` fix above; confirm `uv run pytest tests/integration/patient tests/integration/practitioner tests/integration/organization -q` passes with the SAME 147/147 result as before this change — this is the regression bar, since none of this should change runtime behavior, only *when* wiring happens.
- Manually run `uv run fastapi dev app/main.py`, confirm `/docs` shows exactly the resources listed in `configs/routes.yaml`, and toggling a resource in that file + restarting the dev server still works the same as today.
- Confirm `discover_routers()`/`discover_di_modules()` produce the same key sets as the old hand-written `_ROUTERS`/`DI_MODULES` registries did, on this codebase's actual router/DI module set — a quick `assert set(discover_routers()) == {<expected 34 names>}` sanity check before deleting the old tables.
