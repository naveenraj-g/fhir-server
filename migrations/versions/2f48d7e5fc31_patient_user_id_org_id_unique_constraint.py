"""patient user_id org_id unique constraint

Revision ID: 2f48d7e5fc31
Revises: f7ddb6e2d78d
Create Date: 2026-07-28 17:47:07.478966

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '2f48d7e5fc31'
down_revision: Union[str, None] = 'f7ddb6e2d78d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint('uq_patient_user_id_org_id', 'patient', ['user_id', 'org_id'])


def downgrade() -> None:
    op.drop_constraint('uq_patient_user_id_org_id', 'patient', type_='unique')
