"""terminology_audit_log_fk_set_null

Revision ID: 9d80c58ab577
Revises: 6acaaf6b41bd
Create Date: 2026-10-08 18:50:36.881105

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9d80c58ab577'
down_revision: Union[str, None] = '6acaaf6b41bd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint('terminology_audit_log_concept_id_fkey', 'terminology_audit_log', type_='foreignkey')
    op.drop_constraint('terminology_audit_log_value_set_id_fkey', 'terminology_audit_log', type_='foreignkey')
    op.drop_constraint('terminology_audit_log_display_override_id_fkey', 'terminology_audit_log', type_='foreignkey')
    op.create_foreign_key('terminology_audit_log_concept_id_fkey', 'terminology_audit_log', 'terminology_concept', ['concept_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('terminology_audit_log_value_set_id_fkey', 'terminology_audit_log', 'terminology_value_set', ['value_set_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('terminology_audit_log_display_override_id_fkey', 'terminology_audit_log', 'terminology_display_override', ['display_override_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    op.drop_constraint('terminology_audit_log_concept_id_fkey', 'terminology_audit_log', type_='foreignkey')
    op.drop_constraint('terminology_audit_log_value_set_id_fkey', 'terminology_audit_log', type_='foreignkey')
    op.drop_constraint('terminology_audit_log_display_override_id_fkey', 'terminology_audit_log', type_='foreignkey')
    op.create_foreign_key('terminology_audit_log_concept_id_fkey', 'terminology_audit_log', 'terminology_concept', ['concept_id'], ['id'])
    op.create_foreign_key('terminology_audit_log_value_set_id_fkey', 'terminology_audit_log', 'terminology_value_set', ['value_set_id'], ['id'])
    op.create_foreign_key('terminology_audit_log_display_override_id_fkey', 'terminology_audit_log', 'terminology_display_override', ['display_override_id'], ['id'])
