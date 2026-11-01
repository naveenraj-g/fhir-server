"""add procedure reference identifier columns

Revision ID: 4e3739b98263
Revises: 822ce95b158f
Create Date: 2026-11-01 16:24:45.244322

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '4e3739b98263'
down_revision: Union[str, None] = '822ce95b158f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _add_fallback_columns(table_name: str, prefix: str) -> None:
    op.add_column(table_name, sa.Column(f'{prefix}_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True))
    op.add_column(table_name, sa.Column(f'{prefix}_identifier_type_system', sa.String(), nullable=True))
    op.add_column(table_name, sa.Column(f'{prefix}_identifier_type_version', sa.String(), nullable=True))
    op.add_column(table_name, sa.Column(f'{prefix}_identifier_type_code', sa.String(), nullable=True))
    op.add_column(table_name, sa.Column(f'{prefix}_identifier_type_display', sa.String(), nullable=True))
    op.add_column(table_name, sa.Column(f'{prefix}_identifier_type_text', sa.String(), nullable=True))
    op.add_column(table_name, sa.Column(f'{prefix}_identifier_type_user_selected', sa.Boolean(), nullable=True))
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
        'identifier_type_user_selected',
        'identifier_type_text',
        'identifier_type_display',
        'identifier_type_code',
        'identifier_type_version',
        'identifier_type_system',
        'identifier_use',
    ]:
        op.drop_column(table_name, f'{prefix}_{suffix}')


def upgrade() -> None:
    # procedure core
    op.alter_column('procedure', 'subject_reference', existing_type=sa.String(), nullable=True)
    op.alter_column('procedure', 'subject_type', existing_type=postgresql.ENUM(name='procedure_subject_reference_type'), nullable=True)
    _add_fallback_columns('procedure', 'subject')
    _add_fallback_columns('procedure', 'encounter')
    _add_fallback_columns('procedure', 'recorder')
    _add_fallback_columns('procedure', 'asserter')
    _add_fallback_columns('procedure', 'location')

    # procedure_based_on
    op.alter_column('procedure_based_on', 'reference_type', existing_type=postgresql.ENUM(name='procedure_based_on_reference_type'), nullable=True)
    _add_fallback_columns('procedure_based_on', 'reference')

    # procedure_part_of
    op.alter_column('procedure_part_of', 'reference_type', existing_type=postgresql.ENUM(name='procedure_part_of_reference_type'), nullable=True)
    _add_fallback_columns('procedure_part_of', 'reference')

    # procedure_reason_reference
    op.alter_column('procedure_reason_reference', 'reference_type', existing_type=postgresql.ENUM(name='procedure_reason_reference_reference_type'), nullable=True)
    _add_fallback_columns('procedure_reason_reference', 'reference')

    # procedure_report
    op.alter_column('procedure_report', 'reference_type', existing_type=postgresql.ENUM(name='procedure_report_reference_type'), nullable=True)
    _add_fallback_columns('procedure_report', 'reference')

    # procedure_complication_detail
    op.alter_column('procedure_complication_detail', 'reference_type', existing_type=postgresql.ENUM(name='procedure_complication_detail_reference_type'), nullable=True)
    _add_fallback_columns('procedure_complication_detail', 'reference')

    # procedure_used_reference
    op.alter_column('procedure_used_reference', 'reference_type', existing_type=postgresql.ENUM(name='procedure_used_reference_reference_type'), nullable=True)
    _add_fallback_columns('procedure_used_reference', 'reference')

    # procedure_performer
    op.alter_column('procedure_performer', 'actor_type', existing_type=postgresql.ENUM(name='procedure_performer_actor_reference_type'), nullable=True)
    _add_fallback_columns('procedure_performer', 'actor')
    _add_fallback_columns('procedure_performer', 'on_behalf_of')

    # procedure_focal_device
    op.alter_column('procedure_focal_device', 'manipulated_type', existing_type=postgresql.ENUM(name='procedure_focal_device_manipulated_reference_type'), nullable=True)
    _add_fallback_columns('procedure_focal_device', 'manipulated')

    # procedure_identifier
    _add_fallback_columns('procedure_identifier', 'assigner')


def downgrade() -> None:
    # procedure_identifier
    _drop_fallback_columns('procedure_identifier', 'assigner')

    # procedure_focal_device
    _drop_fallback_columns('procedure_focal_device', 'manipulated')
    op.alter_column('procedure_focal_device', 'manipulated_type', existing_type=postgresql.ENUM(name='procedure_focal_device_manipulated_reference_type'), nullable=False)

    # procedure_performer
    _drop_fallback_columns('procedure_performer', 'on_behalf_of')
    _drop_fallback_columns('procedure_performer', 'actor')
    op.alter_column('procedure_performer', 'actor_type', existing_type=postgresql.ENUM(name='procedure_performer_actor_reference_type'), nullable=False)

    # procedure_used_reference
    _drop_fallback_columns('procedure_used_reference', 'reference')
    op.alter_column('procedure_used_reference', 'reference_type', existing_type=postgresql.ENUM(name='procedure_used_reference_reference_type'), nullable=False)

    # procedure_complication_detail
    _drop_fallback_columns('procedure_complication_detail', 'reference')
    op.alter_column('procedure_complication_detail', 'reference_type', existing_type=postgresql.ENUM(name='procedure_complication_detail_reference_type'), nullable=False)

    # procedure_report
    _drop_fallback_columns('procedure_report', 'reference')
    op.alter_column('procedure_report', 'reference_type', existing_type=postgresql.ENUM(name='procedure_report_reference_type'), nullable=False)

    # procedure_reason_reference
    _drop_fallback_columns('procedure_reason_reference', 'reference')
    op.alter_column('procedure_reason_reference', 'reference_type', existing_type=postgresql.ENUM(name='procedure_reason_reference_reference_type'), nullable=False)

    # procedure_part_of
    _drop_fallback_columns('procedure_part_of', 'reference')
    op.alter_column('procedure_part_of', 'reference_type', existing_type=postgresql.ENUM(name='procedure_part_of_reference_type'), nullable=False)

    # procedure_based_on
    _drop_fallback_columns('procedure_based_on', 'reference')
    op.alter_column('procedure_based_on', 'reference_type', existing_type=postgresql.ENUM(name='procedure_based_on_reference_type'), nullable=False)

    # procedure core
    _drop_fallback_columns('procedure', 'location')
    _drop_fallback_columns('procedure', 'asserter')
    _drop_fallback_columns('procedure', 'recorder')
    _drop_fallback_columns('procedure', 'encounter')
    _drop_fallback_columns('procedure', 'subject')
    op.alter_column('procedure', 'subject_type', existing_type=postgresql.ENUM(name='procedure_subject_reference_type'), nullable=False)
    op.alter_column('procedure', 'subject_reference', existing_type=sa.String(), nullable=False)
