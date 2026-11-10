"""drop terminology display override and audit log tables

Revision ID: 6124e6e77d41
Revises: 1dc9a9c35da9
Create Date: 2026-11-07 00:50:51.974906

Removes terminology_audit_log and terminology_display_override — both
empty in every environment this was checked against (dev DB confirmed 0
rows in each before writing this migration). Not a tech-debt cleanup:
the terminology subsystem is being rebuilt to actually follow the FHIR
R4 terminology module (see docs/terminology-service/08-fhir-r4-standard-
compliance-gap-analysis.md), and both features are explicitly deferred
rather than carried forward half-built — audit logging is going to be
designed once, app-wide, instead of a terminology-only version now and a
second real one later; display overrides return once that's settled.

terminology_audit_log is dropped first since it FK's onto
terminology_display_override (ondelete="SET NULL", so Postgres would
allow dropping either order, but this still reads correctly top-down).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '6124e6e77d41'
down_revision: Union[str, None] = '1dc9a9c35da9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index(op.f('ix_terminology_audit_log_value_set_id'), table_name='terminology_audit_log')
    op.drop_index(op.f('ix_terminology_audit_log_display_override_id'), table_name='terminology_audit_log')
    op.drop_index(op.f('ix_terminology_audit_log_concept_id'), table_name='terminology_audit_log')
    op.drop_index(op.f('ix_terminology_audit_log_action'), table_name='terminology_audit_log')
    op.drop_table('terminology_audit_log')

    op.drop_index(op.f('ix_terminology_display_override_org_id'), table_name='terminology_display_override')
    op.drop_index(op.f('ix_terminology_display_override_concept_id'), table_name='terminology_display_override')
    op.drop_table('terminology_display_override')


def downgrade() -> None:
    op.create_table('terminology_display_override',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('concept_id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.String(), nullable=False),
        sa.Column('display', sa.String(), nullable=False),
        sa.Column('definition', sa.Text(), nullable=True),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['concept_id'], ['terminology_concept.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('concept_id', 'org_id'),
    )
    op.create_index(op.f('ix_terminology_display_override_concept_id'), 'terminology_display_override', ['concept_id'], unique=False)
    op.create_index(op.f('ix_terminology_display_override_org_id'), 'terminology_display_override', ['org_id'], unique=False)

    op.create_table('terminology_audit_log',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('concept_id', sa.Integer(), nullable=True),
        sa.Column('value_set_id', sa.Integer(), nullable=True),
        sa.Column('display_override_id', sa.Integer(), nullable=True),
        sa.Column('performed_by', sa.String(), nullable=True),
        sa.Column('old_value', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('new_value', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['concept_id'], ['terminology_concept.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['display_override_id'], ['terminology_display_override.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['value_set_id'], ['terminology_value_set.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_terminology_audit_log_action'), 'terminology_audit_log', ['action'], unique=False)
    op.create_index(op.f('ix_terminology_audit_log_concept_id'), 'terminology_audit_log', ['concept_id'], unique=False)
    op.create_index(op.f('ix_terminology_audit_log_display_override_id'), 'terminology_audit_log', ['display_override_id'], unique=False)
    op.create_index(op.f('ix_terminology_audit_log_value_set_id'), 'terminology_audit_log', ['value_set_id'], unique=False)
