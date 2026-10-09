"""enforce fhir_profile scope invariants

Revision ID: 7f3543425760
Revises: 9d80c58ab577
Create Date: 2026-10-09 16:02:25.293156

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7f3543425760'
down_revision: Union[str, None] = '9d80c58ab577'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index('uq_fhir_profile_active_scoped', 'fhir_profile', ['resource_type', 'scope_level', 'scope_id'], unique=True, postgresql_where=sa.text("status = 'active' AND scope_id IS NOT NULL"))
    op.create_index('uq_fhir_profile_base_singleton', 'fhir_profile', ['resource_type'], unique=True, postgresql_where=sa.text('scope_id IS NULL'))


def downgrade() -> None:
    op.drop_index('uq_fhir_profile_base_singleton', table_name='fhir_profile', postgresql_where=sa.text('scope_id IS NULL'))
    op.drop_index('uq_fhir_profile_active_scoped', table_name='fhir_profile', postgresql_where=sa.text("status = 'active' AND scope_id IS NOT NULL"))
