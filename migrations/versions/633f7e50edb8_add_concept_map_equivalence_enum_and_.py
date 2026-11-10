"""add concept map equivalence enum and closure tables

Revision ID: 633f7e50edb8
Revises: 6124e6e77d41
Create Date: 2026-11-07 01:20:13.713471

Replaces TerminologyConceptMap.mapping_type (free string) with the real
FHIR ConceptMap.group.element.target.equivalence required-binding enum
(10 values) — see docs/terminology-service/09-fhir-r4-terminology-standard-
reference.md §4.2. terminology_concept_map was truncated (empty) before
this migration, so this is a plain drop+add, not a data-preserving rename.

Also adds the two tables backing the `$closure` operation's server-side
state (terminology_closure_table, terminology_closure_concept) — see
that same doc's §4.4.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '633f7e50edb8'
down_revision: Union[str, None] = '6124e6e77d41'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_EQUIVALENCE_VALUES = (
    "relatedto",
    "equivalent",
    "equal",
    "wider",
    "subsumes",
    "narrower",
    "specializes",
    "inexact",
    "unmatched",
    "disjoint",
)


def upgrade() -> None:
    equivalence_enum = postgresql.ENUM(
        *_EQUIVALENCE_VALUES, name="concept_map_equivalence"
    )
    equivalence_enum.create(op.get_bind(), checkfirst=True)

    op.drop_constraint(
        "terminology_concept_map_source_concept_id_target_concept_id_key",
        "terminology_concept_map",
        type_="unique",
    )
    op.drop_column("terminology_concept_map", "mapping_type")
    op.add_column(
        "terminology_concept_map",
        sa.Column(
            "equivalence",
            postgresql.ENUM(
                *_EQUIVALENCE_VALUES, name="concept_map_equivalence", create_type=False
            ),
            nullable=False,
        ),
    )
    op.create_unique_constraint(
        "terminology_concept_map_source_concept_id_target_concept_id_key",
        "terminology_concept_map",
        ["source_concept_id", "target_concept_id", "equivalence"],
    )

    op.create_table(
        "terminology_closure_table",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("version", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(
        op.f("ix_terminology_closure_table_name"),
        "terminology_closure_table",
        ["name"],
        unique=False,
    )

    op.create_table(
        "terminology_closure_concept",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("closure_table_id", sa.Integer(), nullable=False),
        sa.Column("concept_id", sa.Integer(), nullable=False),
        sa.Column("added_at_version", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["closure_table_id"], ["terminology_closure_table.id"]
        ),
        sa.ForeignKeyConstraint(["concept_id"], ["terminology_concept.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("closure_table_id", "concept_id"),
    )
    op.create_index(
        op.f("ix_terminology_closure_concept_closure_table_id"),
        "terminology_closure_concept",
        ["closure_table_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_terminology_closure_concept_concept_id"),
        "terminology_closure_concept",
        ["concept_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_terminology_closure_concept_added_at_version"),
        "terminology_closure_concept",
        ["added_at_version"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_terminology_closure_concept_added_at_version"),
        table_name="terminology_closure_concept",
    )
    op.drop_index(
        op.f("ix_terminology_closure_concept_concept_id"),
        table_name="terminology_closure_concept",
    )
    op.drop_index(
        op.f("ix_terminology_closure_concept_closure_table_id"),
        table_name="terminology_closure_concept",
    )
    op.drop_table("terminology_closure_concept")

    op.drop_index(
        op.f("ix_terminology_closure_table_name"), table_name="terminology_closure_table"
    )
    op.drop_table("terminology_closure_table")

    op.drop_constraint(
        "terminology_concept_map_source_concept_id_target_concept_id_key",
        "terminology_concept_map",
        type_="unique",
    )
    op.drop_column("terminology_concept_map", "equivalence")
    op.add_column(
        "terminology_concept_map",
        sa.Column("mapping_type", sa.String(), nullable=True),
    )
    op.create_unique_constraint(
        "terminology_concept_map_source_concept_id_target_concept_i_key",
        "terminology_concept_map",
        ["source_concept_id", "target_concept_id", "mapping_type"],
    )

    postgresql.ENUM(*_EQUIVALENCE_VALUES, name="concept_map_equivalence").drop(
        op.get_bind(), checkfirst=True
    )
