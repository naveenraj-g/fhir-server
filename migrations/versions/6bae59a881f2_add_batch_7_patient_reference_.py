"""add batch 7 patient reference identifier fallback columns

Revision ID: 6bae59a881f2
Revises: 40284fb8caf3
Create Date: 2026-11-01 22:25:26.176966

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6bae59a881f2'
down_revision: Union[str, None] = '40284fb8caf3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1. Patient ─────────────────────────────────────────────────────────────
    # patient: add 7 missing fallback columns to managing_organization_identifier_*
    op.add_column('patient', sa.Column('managing_organization_identifier_type_system', sa.String(), nullable=True))
    op.add_column('patient', sa.Column('managing_organization_identifier_type_version', sa.String(), nullable=True))
    op.add_column('patient', sa.Column('managing_organization_identifier_type_code', sa.String(), nullable=True))
    op.add_column('patient', sa.Column('managing_organization_identifier_type_display', sa.String(), nullable=True))
    op.add_column('patient', sa.Column('managing_organization_identifier_type_user_selected', sa.Boolean(), nullable=True))
    op.add_column('patient', sa.Column('managing_organization_identifier_period_start', sa.DateTime(timezone=True), nullable=True))
    op.add_column('patient', sa.Column('managing_organization_identifier_period_end', sa.DateTime(timezone=True), nullable=True))

    # patient_contact: add 7 missing fallback columns to organization_identifier_*
    op.add_column('patient_contact', sa.Column('organization_identifier_type_system', sa.String(), nullable=True))
    op.add_column('patient_contact', sa.Column('organization_identifier_type_version', sa.String(), nullable=True))
    op.add_column('patient_contact', sa.Column('organization_identifier_type_code', sa.String(), nullable=True))
    op.add_column('patient_contact', sa.Column('organization_identifier_type_display', sa.String(), nullable=True))
    op.add_column('patient_contact', sa.Column('organization_identifier_type_user_selected', sa.Boolean(), nullable=True))
    op.add_column('patient_contact', sa.Column('organization_identifier_period_start', sa.DateTime(timezone=True), nullable=True))
    op.add_column('patient_contact', sa.Column('organization_identifier_period_end', sa.DateTime(timezone=True), nullable=True))

    # patient_general_practitioner: add 7 missing fallback columns to reference_identifier_*
    op.add_column('patient_general_practitioner', sa.Column('reference_identifier_type_system', sa.String(), nullable=True))
    op.add_column('patient_general_practitioner', sa.Column('reference_identifier_type_version', sa.String(), nullable=True))
    op.add_column('patient_general_practitioner', sa.Column('reference_identifier_type_code', sa.String(), nullable=True))
    op.add_column('patient_general_practitioner', sa.Column('reference_identifier_type_display', sa.String(), nullable=True))
    op.add_column('patient_general_practitioner', sa.Column('reference_identifier_type_user_selected', sa.Boolean(), nullable=True))
    op.add_column('patient_general_practitioner', sa.Column('reference_identifier_period_start', sa.DateTime(timezone=True), nullable=True))
    op.add_column('patient_general_practitioner', sa.Column('reference_identifier_period_end', sa.DateTime(timezone=True), nullable=True))

    # patient_link: add 7 missing fallback columns to other_identifier_*
    op.add_column('patient_link', sa.Column('other_identifier_type_system', sa.String(), nullable=True))
    op.add_column('patient_link', sa.Column('other_identifier_type_version', sa.String(), nullable=True))
    op.add_column('patient_link', sa.Column('other_identifier_type_code', sa.String(), nullable=True))
    op.add_column('patient_link', sa.Column('other_identifier_type_display', sa.String(), nullable=True))
    op.add_column('patient_link', sa.Column('other_identifier_type_user_selected', sa.Boolean(), nullable=True))
    op.add_column('patient_link', sa.Column('other_identifier_period_start', sa.DateTime(timezone=True), nullable=True))
    op.add_column('patient_link', sa.Column('other_identifier_period_end', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    for col in (
        'other_identifier_period_end',
        'other_identifier_period_start',
        'other_identifier_type_user_selected',
        'other_identifier_type_display',
        'other_identifier_type_code',
        'other_identifier_type_version',
        'other_identifier_type_system',
    ):
        op.drop_column('patient_link', col)

    for col in (
        'reference_identifier_period_end',
        'reference_identifier_period_start',
        'reference_identifier_type_user_selected',
        'reference_identifier_type_display',
        'reference_identifier_type_code',
        'reference_identifier_type_version',
        'reference_identifier_type_system',
    ):
        op.drop_column('patient_general_practitioner', col)

    for col in (
        'organization_identifier_period_end',
        'organization_identifier_period_start',
        'organization_identifier_type_user_selected',
        'organization_identifier_type_display',
        'organization_identifier_type_code',
        'organization_identifier_type_version',
        'organization_identifier_type_system',
    ):
        op.drop_column('patient_contact', col)

    for col in (
        'managing_organization_identifier_period_end',
        'managing_organization_identifier_period_start',
        'managing_organization_identifier_type_user_selected',
        'managing_organization_identifier_type_display',
        'managing_organization_identifier_type_code',
        'managing_organization_identifier_type_version',
        'managing_organization_identifier_type_system',
    ):
        op.drop_column('patient', col)
