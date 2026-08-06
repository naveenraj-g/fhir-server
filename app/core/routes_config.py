from pathlib import Path

import yaml


def load_enabled_routes(path: str) -> set[str]:
    """Reads the routes.yaml `routes:` block, returns the set of enabled
    resource names. Missing file or missing `routes:` key is a hard startup
    error — fail fast rather than silently exposing everything or nothing."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Routes config not found: {path}")

    data = yaml.safe_load(p.read_text()) or {}
    routes = data.get("routes")
    if routes is None:
        raise ValueError(f"{path} is missing a top-level 'routes:' key")

    return {name for name, on in routes.items() if on}
