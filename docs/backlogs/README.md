# Backlogs

Work we've agreed to do later. Each file is one backlog; tick an item when it's implemented.

## [fhir-search.md](fhir-search.md) — FHIR R4 search gaps

- [ ] 1. Store client `meta`, and search it: `_tag`, `_profile`, `_security`, `_source`
- [ ] 2. Endpoint resource (enables Endpoint reference checks, `_include=Organization:endpoint`,
      `endpoint.<param>` chaining)
- [ ] 3. `_revinclude` / `_has` from resources that reference Organization
- [ ] 4. `_text` / `_content` (full-text search)
- [ ] 5. `_filter`
- [ ] 6. `_list`, `_type`, `_contained`
