"""Shared path exclusions for middleware that shouldn't act on health probes,
docs UIs, or the root/favicon — RateLimitMiddleware and AccessLogMiddleware
both need this same set. Previously each kept its own independently
hand-maintained copy, and they'd already drifted apart (rate_limit excluded
"/", access_log didn't; access_log matched "/favicon.ico" exactly, rate_limit
matched any "/favicon*" prefix) with no reason for the difference.
"""

EXCLUDED_PATHS: frozenset[str] = frozenset(
    {"/", "/health", "/health/ready", "/openapi.json", "/favicon.ico"}
)
EXCLUDED_PREFIXES: tuple[str, ...] = ("/docs", "/redoc")
