# Organization Postman test payloads

All bodies are for `POST /api/fhir/v1/organizations` (or `PATCH .../organizations/{id}`
where noted) using `Accept: application/json` (plain snake_case). Organization is one of
the three JWT-authenticated resources — send a valid `Authorization: Bearer <token>`
whose claims include `activeOrganizationId` and the right `organization:*` permission
scope. `org_id` and `created_by`/`updated_by` come from that token, never from the body.

## Files

- `01_minimal.json` — smallest valid create (just `active` + `name`, no sub-resources).
- `02_full_single.json` — one organization exercising every sub-resource
  (identifier, type, alias, telecom, address, contact + nested telecom, endpoint).
- `08_identifier_only.json` / `09_type_only.json` / `10_alias_only.json` /
  `11_telecom_only.json` / `12_address_only.json` / `13_contact_only.json` /
  `14_endpoint_only.json` — isolated single-sub-resource creates, useful for narrowing
  down a failure to one mapper/schema.
- `15_partof_logical_reference_only.json` — `partOf` expressed purely as the
  `partof_identifier_*` fallback (no `partof` reference string) — for when the parent
  organization isn't itself a resource in this system.
- `16_patch_attach_to_parent.json` — PATCH body that attaches an existing organization
  to a parent after the fact (alternative to setting `partof` at create time).
- `17_inactive_organization.json` — `active: false` edge case.

## Multi-level hierarchy (`hierarchy_*` files)

These four build a 3-level tree plus a sibling, to exercise `partOf`:

```
03_hierarchy_parent.json            (top-level, no partof)
└── 04_hierarchy_child.json         (partof -> parent)
    └── 05_hierarchy_grandchild.json (partof -> child)
06_hierarchy_sibling.json           (partof -> parent, sibling of child)
```

**Run them in order and patch in real IDs as you go** — `partof` needs a real
`Organization/<organization_id>` reference, so you can't fire all four in parallel:

1. POST `03_hierarchy_parent.json` → note the returned `id` (e.g. `190010`).
2. In `04_hierarchy_child.json`, replace `"Organization/REPLACE_PARENT_ID"` with
   `"Organization/190010"`, then POST it → note its `id` (e.g. `190011`).
3. In `06_hierarchy_sibling.json`, replace `"Organization/REPLACE_PARENT_ID"` with the
   same parent id (`190010`), then POST it.
4. In `05_hierarchy_grandchild.json`, replace `"Organization/REPLACE_CHILD_ID"` with the
   child's id (`190011`), then POST it.

Result: one parent, two children (one of which has its own child), letting you test
`GET /organizations/{id}` at every level and confirm `partOf` resolves correctly, plus
the cycle-check business logic (try setting a parent's `partof` to one of its own
descendants afterward via PATCH — it should be rejected).
