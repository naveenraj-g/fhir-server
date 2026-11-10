"""ConceptMap's `$translate` and `$closure` operations — see
docs/terminology-service/09-fhir-r4-terminology-standard-reference.md
§4.3-4.4. Kept separate from the existing, non-standard `/translate`
endpoint (`app/services/terminology/validation.py`'s `translate()`) rather
than folded into it — these build real FHIR `Parameters`/`ConceptMap`-shaped
output and have a different input contract (`$translate` supports
`reverse`; `$closure` is a wholly different, stateful operation with no
non-standard precedent at all). The old endpoint is untouched; these are
new, additional routes."""

from datetime import UTC, datetime

from app.fhir.parameters import (
    build_parameters,
    param_boolean,
    param_code,
    param_coding,
    param_part,
    param_string,
)

# $closure's own `equivalence` output is restricted to equal/specializes/
# subsumes/unmatched (never "subsumed-by", unlike $subsumes) — see
# app/repository/terminology/hierarchy.py's subsumption_relationship()
# docstring, which this mapping implements for the ConceptMap side.
# "disjoint" has no entry: a disjoint pair is skipped entirely rather than
# emitted as an explicit "unmatched" target — $closure only ever reports
# relationships that actually exist, not every non-relationship.
_CLOSURE_EQUIVALENCE = {
    "equal": "equal",
    "a_subsumes_b": "subsumes",
    "b_subsumes_a": "specializes",
}


class _ConceptMapOperationsMixin:
    async def translate_operation(
        self,
        system: str,
        code: str,
        targetsystem: str | None,
        reverse: bool,
    ) -> dict:
        """Returns a `Parameters` resource dict (§4.3). Resolves strictly by
        source+target system/code, never by a ConceptMap canonical URL —
        see `TerminologyConceptMap`'s own docstring
        (app/models/terminology/terminology.py) for why no such thing
        exists to address yet."""
        _src_cs, src_concept = await self.repository.lookup_concept(system, code)
        if src_concept is None:
            return build_parameters(
                param_boolean("result", False),
                param_string("message", f"No concept found for {system}|{code}."),
            )

        if reverse:
            rows = await self.repository.get_reverse_translations(
                src_concept.id, targetsystem
            )
        else:
            rows = await self.repository.get_translations(src_concept.id, targetsystem)

        matches = [
            param_part(
                "match",
                param_code("equivalence", cm.equivalence.value),
                param_coding(
                    "concept",
                    {
                        "system": other_cs.canonical_url,
                        "code": other_concept.code,
                        "display": other_concept.display,
                    },
                ),
            )
            for cm, other_concept, other_cs in rows
        ]

        # result=true only when at least one match is a real equivalence,
        # not just unmatched/disjoint — see §4.2's own rule.
        real_matches = [
            cm for cm, _concept, _cs in rows
            if cm.equivalence.value not in ("unmatched", "disjoint")
        ]
        result = len(real_matches) > 0

        message = None
        if not rows:
            suffix = f" to {targetsystem}" if targetsystem else ""
            message = f"No mapping found for {system}|{code}{suffix}."
        elif not result:
            message = (
                "Mapping(s) found, but none represent a real equivalence "
                "(unmatched/disjoint only)."
            )

        return build_parameters(
            param_boolean("result", result),
            param_string("message", message),
            *matches,
        )

    async def _relationship_pairs(
        self, subject_concept, subject_cs, others: list[tuple]
    ) -> list[tuple]:
        """`subject` plays the ConceptMap `element.code` (source) role;
        each `other` with a real IS-A relationship to it becomes one of its
        `target[]` entries. Skips self-pairs and disjoint/no-relationship
        pairs (see `_CLOSURE_EQUIVALENCE`'s own comment above)."""
        pairs = []
        for other_concept, other_cs in others:
            if other_concept.id == subject_concept.id:
                continue
            raw = await self.repository.subsumption_relationship(
                other_concept.id, subject_concept.id
            )
            equivalence = _CLOSURE_EQUIVALENCE.get(raw)
            if equivalence is None:
                continue
            pairs.append(
                (subject_concept, subject_cs, other_concept, other_cs, equivalence)
            )
        return pairs

    def _closure_conceptmap(self, name: str, version: int, pairs: list[tuple]) -> dict:
        """Builds the `ConceptMap` resource `$closure` returns directly
        (§4.4) — NOT wrapped in `Parameters`, unlike every other operation
        here. `pairs`: list of (src_concept, src_cs, tgt_concept, tgt_cs,
        equivalence_str). `group` is omitted entirely (not `"group": []`)
        when there's nothing to report — matches the spec's own
        initialize/no-op response shape."""
        body = {
            "resourceType": "ConceptMap",
            "id": name,
            "version": str(version),
            "status": "active",
            "experimental": False,
            "date": datetime.now(UTC).isoformat(),
        }
        if not pairs:
            return body

        groups: dict[tuple[str, str], dict[str, dict]] = {}
        for src_concept, src_cs, tgt_concept, tgt_cs, equivalence in pairs:
            key = (src_cs.canonical_url, tgt_cs.canonical_url)
            elements = groups.setdefault(key, {})
            element = elements.setdefault(
                src_concept.code, {"code": src_concept.code, "target": []}
            )
            element["target"].append(
                {"code": tgt_concept.code, "equivalence": equivalence}
            )
        body["group"] = [
            {"source": src_url, "target": tgt_url, "element": list(elements.values())}
            for (src_url, tgt_url), elements in groups.items()
        ]
        return body

    async def closure_operation(
        self, name: str, concepts: list[dict], version: str | None
    ) -> dict:
        """`concepts`: list of `{"system": ..., "code": ...}` dicts, already
        extracted from `Coding` parameters by the router. See §4.4 and
        `app/repository/terminology/closure.py`'s own docstrings for the
        state this reads/writes."""
        table = await self.repository.get_closure_table(name)
        if table is None:
            table = await self.repository.create_closure_table(name)

        if version is not None:
            since = int(version)
            additions = await self.repository.get_closure_additions_since(
                table.id, since
            )
            if not additions:
                return self._closure_conceptmap(name, table.version, [])
            all_members = await self.repository.get_closure_members(table.id)
            pairs: list[tuple] = []
            for add_concept, add_cs, _added_version in additions:
                pairs += await self._relationship_pairs(
                    add_concept, add_cs, all_members
                )
            return self._closure_conceptmap(name, table.version, pairs)

        if not concepts:
            # (Re)initialize: zero concepts, no version — wipe membership,
            # reset to version 0. A no-op on an already-fresh table (avoids
            # a pointless extra round-trip right after create_closure_table).
            if table.version != 0:
                await self.repository.reinitialize_closure_table(table.id)
            return self._closure_conceptmap(name, 0, [])

        existing_members = await self.repository.get_closure_members(table.id)
        existing_ids = {c.id for c, _cs in existing_members}

        resolved: list[tuple] = []
        seen_ids: set[int] = set()
        for c in concepts:
            _cs, concept = await self.repository.lookup_concept(c["system"], c["code"])
            if concept is None or concept.id in existing_ids or concept.id in seen_ids:
                continue
            seen_ids.add(concept.id)
            resolved.append((concept, _cs))

        if not resolved:
            return self._closure_conceptmap(name, table.version, [])

        pairs = []
        for new_concept, new_cs in resolved:
            pairs += await self._relationship_pairs(
                new_concept, new_cs, existing_members
            )
        for i, (new_concept, new_cs) in enumerate(resolved):
            pairs += await self._relationship_pairs(
                new_concept, new_cs, resolved[i + 1 :]
            )

        new_version = table.version + 1
        await self.repository.add_closure_members(
            table.id, [c.id for c, _cs in resolved], new_version
        )
        return self._closure_conceptmap(name, new_version, pairs)
