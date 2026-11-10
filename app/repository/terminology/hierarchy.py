from sqlalchemy import text


class _HierarchyMixin:
    """Backs both CodeSystem's `$subsumes` and ConceptMap's `$closure` —
    see docs/terminology-service/09-fhir-r4-terminology-standard-reference.md
    §2.6 and §4.4. Both operations ultimately ask the same structural
    question (how do two concepts relate in the IS-A hierarchy?) and then
    translate the answer into their own, different output vocabulary —
    subsumption_relationship() below answers the question once, each
    operation's own service method does the translation.

    TerminologyRelationship (app/models/terminology/terminology.py) only
    stores DIRECT parent/child edges, not a precomputed transitive closure
    — SNOMED CT's loader (app/terminology/import_/loaders/snomed.py)
    populates one row per direct IS-A edge, same as the source data. A
    multi-level ancestor (grandparent, etc.) is therefore only findable by
    walking the chain, which is_ancestor() below does via a recursive CTE
    rather than N round-trips."""

    async def is_ancestor(
        self,
        descendant_concept_id: int,
        ancestor_concept_id: int,
        max_depth: int = 50,
    ) -> bool:
        """True if `ancestor_concept_id` is reachable by walking
        parent_concept_id links upward from `descendant_concept_id`, any
        number of hops up to max_depth (50 is comfortably deeper than any
        real SNOMED CT IS-A chain) — i.e. "ancestor subsumes descendant"."""
        async with self.session_factory() as session:
            result = await session.execute(
                text(
                    """
                    WITH RECURSIVE ancestors AS (
                        SELECT parent_concept_id AS ancestor_id, 1 AS depth
                        FROM terminology_relationship
                        WHERE child_concept_id = :descendant_id
                          AND relationship_type = 'is-a'
                        UNION ALL
                        SELECT r.parent_concept_id, a.depth + 1
                        FROM terminology_relationship r
                        JOIN ancestors a ON r.child_concept_id = a.ancestor_id
                        WHERE r.relationship_type = 'is-a'
                          AND a.depth < :max_depth
                    )
                    SELECT EXISTS (
                        SELECT 1 FROM ancestors WHERE ancestor_id = :ancestor_id
                    )
                    """
                ),
                {
                    "descendant_id": descendant_concept_id,
                    "ancestor_id": ancestor_concept_id,
                    "max_depth": max_depth,
                },
            )
            return bool(result.scalar())

    async def subsumption_relationship(
        self, concept_id_a: int, concept_id_b: int
    ) -> str:
        """Returns one of "equal" / "a_subsumes_b" / "b_subsumes_a" /
        "disjoint" — the raw structural relationship between two concepts,
        walked transitively via is_ancestor() above (direct IS-A edges
        only; "part-of" and any other TerminologyRelationship.relationship_type
        value are deliberately NOT subsumption and are ignored here).

        Callers translate this into their own operation's vocabulary:
        - `$subsumes` (CodeSystem): equal->equivalent, a_subsumes_b->subsumes,
          b_subsumes_a->subsumed-by, disjoint->not-subsumed
        - `$closure` (ConceptMap): equal->equal, a_subsumes_b->subsumes,
          b_subsumes_a->specializes, disjoint->unmatched
          (per docs/terminology-service/09-...md §4.4: closure's own
          `equivalence` output is restricted to equal/specializes/subsumes/
          unmatched — it never emits "subsumed-by", unlike $subsumes.)

        Which of A/B is "new" vs. "existing", or "source" vs. "target", is
        entirely the caller's own convention — this function is symmetric
        and just answers the structural question for the two ids given."""
        if concept_id_a == concept_id_b:
            return "equal"
        if await self.is_ancestor(
            descendant_concept_id=concept_id_b, ancestor_concept_id=concept_id_a
        ):
            return "a_subsumes_b"
        if await self.is_ancestor(
            descendant_concept_id=concept_id_a, ancestor_concept_id=concept_id_b
        ):
            return "b_subsumes_a"
        return "disjoint"
