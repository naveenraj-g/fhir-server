"""convert_location_alias_to_array_column

Location.alias was a child table (location_alias) for what is really just a
0..* string list; converted to a plain ARRAY(String) column on the main row,
per the established "no comma-Text exception for 0..* scalar lists" rule —
same conversion Organization.alias already went through. Data-preserving:
existing location_alias rows are folded into the new array column (ordered
by id, so insertion order survives), then the child table is dropped.

Revision ID: a681823da147
Revises: 2f885e170956
Create Date: 2026-10-29 20:17:50.454532

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'a681823da147'
down_revision: Union[str, None] = '2f885e170956'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('location', sa.Column('alias', postgresql.ARRAY(sa.String()), nullable=True))

    op.execute(
        """
        UPDATE location
        SET alias = sub.values
        FROM (
            SELECT location_pk, array_agg(value ORDER BY id) AS values
            FROM location_alias
            GROUP BY location_pk
        ) AS sub
        WHERE location.id = sub.location_pk
        """
    )

    op.drop_index(op.f('ix_location_alias_updated_at'), table_name='location_alias')
    op.drop_index(op.f('ix_location_alias_tenant_id'), table_name='location_alias')
    op.drop_index(op.f('ix_location_alias_location_pk'), table_name='location_alias')
    op.drop_index(op.f('ix_location_alias_created_at'), table_name='location_alias')
    op.drop_table('location_alias')


def downgrade() -> None:
    op.create_table(
        'location_alias',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('location_pk', sa.BigInteger(), nullable=False),
        sa.Column('value', sa.String(), nullable=False),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['location_pk'], ['location.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_location_alias_created_at'), 'location_alias', ['created_at'], unique=False)
    op.create_index(op.f('ix_location_alias_location_pk'), 'location_alias', ['location_pk'], unique=False)
    op.create_index(op.f('ix_location_alias_tenant_id'), 'location_alias', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_location_alias_updated_at'), 'location_alias', ['updated_at'], unique=False)

    # created_by has no per-alias source anymore — fall back to the owning
    # location's own created_by, same spirit as a best-effort downgrade.
    op.execute(
        """
        INSERT INTO location_alias (location_pk, value, tenant_id, created_by, created_at)
        SELECT l.id, a.value, l.tenant_id, l.created_by, now()
        FROM location l
        CROSS JOIN LATERAL unnest(l.alias) WITH ORDINALITY AS a(value, ord)
        WHERE l.alias IS NOT NULL
        ORDER BY l.id, a.ord
        """
    )

    op.drop_column('location', 'alias')
