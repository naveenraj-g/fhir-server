"""patient org_id and identifier system mandatory

Revision ID: f7ddb6e2d78d
Revises: 14b3d5b6c776
Create Date: 2026-07-28 12:13:34.397835

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'f7ddb6e2d78d'
down_revision: Union[str, None] = '14b3d5b6c776'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('patient', 'org_id',
               existing_type=sa.VARCHAR(),
               nullable=False)
    op.alter_column('patient_identifier', 'system',
               existing_type=sa.VARCHAR(),
               nullable=False)
    op.create_unique_constraint(None, 'patient_identifier', ['system', 'value'])


def downgrade() -> None:
    op.drop_constraint(None, 'patient_identifier', type_='unique')
    op.alter_column('patient_identifier', 'system',
               existing_type=sa.VARCHAR(),
               nullable=True)
    op.alter_column('patient', 'org_id',
               existing_type=sa.VARCHAR(),
               nullable=True)
