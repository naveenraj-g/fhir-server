"""add_terminology_display_override

Revision ID: 6acaaf6b41bd
Revises: b9a8062d2098
Create Date: 2026-10-08 18:40:16.526855

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6acaaf6b41bd'
down_revision: Union[str, None] = 'b9a8062d2098'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
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
    sa.UniqueConstraint('concept_id', 'org_id')
    )
    op.create_index(op.f('ix_terminology_display_override_concept_id'), 'terminology_display_override', ['concept_id'], unique=False)
    op.create_index(op.f('ix_terminology_display_override_org_id'), 'terminology_display_override', ['org_id'], unique=False)
    op.add_column('terminology_audit_log', sa.Column('display_override_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_terminology_audit_log_display_override_id'), 'terminology_audit_log', ['display_override_id'], unique=False)
    op.create_foreign_key(None, 'terminology_audit_log', 'terminology_display_override', ['display_override_id'], ['id'])


def downgrade() -> None:
    op.drop_constraint(None, 'terminology_audit_log', type_='foreignkey')
    op.drop_index(op.f('ix_terminology_audit_log_display_override_id'), table_name='terminology_audit_log')
    op.drop_column('terminology_audit_log', 'display_override_id')
    op.drop_index(op.f('ix_terminology_display_override_org_id'), table_name='terminology_display_override')
    op.drop_index(op.f('ix_terminology_display_override_concept_id'), table_name='terminology_display_override')
    op.drop_table('terminology_display_override')
