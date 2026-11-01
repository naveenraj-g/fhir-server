"""add care_team reference identifier fallback columns

Revision ID: 26c08b471f6d
Revises: 4e3739b98263
Create Date: 2026-11-01 18:06:59.920606

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '26c08b471f6d'
down_revision: Union[str, None] = '4e3739b98263'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _add_fallback_columns(table_name: str, prefix: str) -> None:
    op.add_column(table_name, sa.Column(f'{prefix}_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True))
    op.add_column(table_name, sa.Column(f'{prefix}_identifier_type_system', sa.String(), nullable=True))
    op.add_column(table_name, sa.Column(f'{prefix}_identifier_type_version', sa.String(), nullable=True))
    op.add_column(table_name, sa.Column(f'{prefix}_identifier_type_code', sa.String(), nullable=True))
    op.add_column(table_name, sa.Column(f'{prefix}_identifier_type_display', sa.String(), nullable=True))
    op.add_column(table_name, sa.Column(f'{prefix}_identifier_type_user_selected', sa.Boolean(), nullable=True))
    op.add_column(table_name, sa.Column(f'{prefix}_identifier_type_text', sa.String(), nullable=True))
    op.add_column(table_name, sa.Column(f'{prefix}_identifier_system', sa.String(), nullable=True))
    op.add_column(table_name, sa.Column(f'{prefix}_identifier_value', sa.String(), nullable=True))
    op.add_column(table_name, sa.Column(f'{prefix}_identifier_period_start', sa.DateTime(timezone=True), nullable=True))
    op.add_column(table_name, sa.Column(f'{prefix}_identifier_period_end', sa.DateTime(timezone=True), nullable=True))


def _drop_fallback_columns(table_name: str, prefix: str) -> None:
    for suffix in [
        'identifier_period_end',
        'identifier_period_start',
        'identifier_value',
        'identifier_system',
        'identifier_type_text',
        'identifier_type_user_selected',
        'identifier_type_display',
        'identifier_type_code',
        'identifier_type_version',
        'identifier_type_system',
        'identifier_use',
    ]:
        op.drop_column(table_name, f'{prefix}_{suffix}')


def upgrade() -> None:
    # care_team
    _add_fallback_columns('care_team', 'subject')
    _add_fallback_columns('care_team', 'encounter')

    # care_team_identifier (add 7 missing columns)
    op.add_column('care_team_identifier', sa.Column('assigner_identifier_type_system', sa.String(), nullable=True))
    op.add_column('care_team_identifier', sa.Column('assigner_identifier_type_version', sa.String(), nullable=True))
    op.add_column('care_team_identifier', sa.Column('assigner_identifier_type_code', sa.String(), nullable=True))
    op.add_column('care_team_identifier', sa.Column('assigner_identifier_type_display', sa.String(), nullable=True))
    op.add_column('care_team_identifier', sa.Column('assigner_identifier_type_user_selected', sa.Boolean(), nullable=True))
    op.add_column('care_team_identifier', sa.Column('assigner_identifier_period_start', sa.DateTime(timezone=True), nullable=True))
    op.add_column('care_team_identifier', sa.Column('assigner_identifier_period_end', sa.DateTime(timezone=True), nullable=True))

    # care_team_participant
    _add_fallback_columns('care_team_participant', 'member')
    _add_fallback_columns('care_team_participant', 'on_behalf_of')

    # care_team_reason_reference
    _add_fallback_columns('care_team_reason_reference', 'reference')

    # care_team_managing_organization
    _add_fallback_columns('care_team_managing_organization', 'reference')


def downgrade() -> None:
    # care_team_managing_organization
    _drop_fallback_columns('care_team_managing_organization', 'reference')

    # care_team_reason_reference
    _drop_fallback_columns('care_team_reason_reference', 'reference')

    # care_team_participant
    _drop_fallback_columns('care_team_participant', 'on_behalf_of')
    _drop_fallback_columns('care_team_participant', 'member')

    # care_team_identifier (drop 7 added columns)
    op.drop_column('care_team_identifier', 'assigner_identifier_period_end')
    op.drop_column('care_team_identifier', 'assigner_identifier_period_start')
    op.drop_column('care_team_identifier', 'assigner_identifier_type_user_selected')
    op.drop_column('care_team_identifier', 'assigner_identifier_type_display')
    op.drop_column('care_team_identifier', 'assigner_identifier_type_code')
    op.drop_column('care_team_identifier', 'assigner_identifier_type_version')
    op.drop_column('care_team_identifier', 'assigner_identifier_type_system')

    # care_team
    _drop_fallback_columns('care_team', 'encounter')
    _drop_fallback_columns('care_team', 'subject')
