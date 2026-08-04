"""drop organization user_id column

Revision ID: 53a9cec9cb00
Revises: 936898518be3
Create Date: 2026-08-04 14:27:12.146869

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '53a9cec9cb00'
down_revision: Union[str, None] = '936898518be3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index(op.f('ix_organization_user_id'), table_name='organization')
    op.drop_column('organization', 'user_id')


def downgrade() -> None:
    op.add_column('organization', sa.Column('user_id', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.create_index(op.f('ix_organization_user_id'), 'organization', ['user_id'], unique=False)
