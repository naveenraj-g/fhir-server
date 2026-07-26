"""consolidate_observation_encounter_enum

Revision ID: 2048fe9a4c8d
Revises: 499918ba7758
Create Date: 2026-07-26 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '2048fe9a4c8d'
down_revision: Union[str, None] = '499918ba7758'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # observation.encounter_type was forked onto its own Postgres enum type
    # (obs_encounter_ref_type) instead of reusing the shared
    # encounter_reference_type type every other Encounter-reference column
    # in the codebase uses. Both types have the identical single value
    # 'Encounter', so this is a straight swap + drop of the orphaned type.
    op.execute(
        "ALTER TABLE observation "
        "ALTER COLUMN encounter_type TYPE encounter_reference_type "
        "USING encounter_type::text::encounter_reference_type"
    )
    op.execute("DROP TYPE obs_encounter_ref_type")


def downgrade() -> None:
    op.execute("CREATE TYPE obs_encounter_ref_type AS ENUM ('Encounter')")
    op.execute(
        "ALTER TABLE observation "
        "ALTER COLUMN encounter_type TYPE obs_encounter_ref_type "
        "USING encounter_type::text::obs_encounter_ref_type"
    )
