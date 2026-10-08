"""drop_vitals_table

Revision ID: b9a8062d2098
Revises: b63b799d606f
Create Date: 2026-10-08 03:09:25.606784

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b9a8062d2098'
down_revision: Union[str, None] = 'b63b799d606f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index(op.f('ix_vitals_id'), table_name='vitals')
    op.drop_index(op.f('ix_vitals_org_id'), table_name='vitals')
    op.drop_index(op.f('ix_vitals_patient_id'), table_name='vitals')
    op.drop_index(op.f('ix_vitals_pseudo_id'), table_name='vitals')
    op.drop_index(op.f('ix_vitals_user_id'), table_name='vitals')
    op.drop_index(op.f('ix_vitals_vitals_id'), table_name='vitals')
    op.drop_table('vitals')
    op.execute('DROP SEQUENCE IF EXISTS vitals_pub_seq')


def downgrade() -> None:
    op.execute("CREATE SEQUENCE IF NOT EXISTS vitals_pub_seq START 70000 INCREMENT 1")
    op.create_table('vitals',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('vitals_id', sa.INTEGER(), server_default=sa.text("nextval('vitals_pub_seq'::regclass)"), autoincrement=True, nullable=False),
    sa.Column('pseudo_id', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('pseudo_id2', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('user_id', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('patient_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('org_id', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('steps', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('calories_kcal', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('distance_meters', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('total_active_minutes', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('activity_name', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('exercise_duration_minutes', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('active_zone_minutes', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('fatburn_active_zone_minutes', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('cardio_active_zone_minutes', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('peak_active_zone_minutes', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('resting_heart_rate', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('heart_rate', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('heart_rate_variability', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('stress_management_score', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('blood_pressure_systolic', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('blood_pressure_diastolic', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('sleep_minutes', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('rem_sleep_minutes', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('deep_sleep_minutes', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('light_sleep_minutes', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('awake_minutes', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('bed_time', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('wake_up_time', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('deep_sleep_percent', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('rem_sleep_percent', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('light_sleep_percent', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('awake_percent', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('weight_kg', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('height_cm', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('age', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('gender', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('recorded_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.Column('date', sa.DATE(), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=True),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.Column('created_by', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('updated_by', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name=op.f('vitals_pkey'))
    )
    op.create_index(op.f('ix_vitals_vitals_id'), 'vitals', ['vitals_id'], unique=True)
    op.create_index(op.f('ix_vitals_user_id'), 'vitals', ['user_id'], unique=False)
    op.create_index(op.f('ix_vitals_pseudo_id'), 'vitals', ['pseudo_id'], unique=False)
    op.create_index(op.f('ix_vitals_patient_id'), 'vitals', ['patient_id'], unique=False)
    op.create_index(op.f('ix_vitals_org_id'), 'vitals', ['org_id'], unique=False)
    op.create_index(op.f('ix_vitals_id'), 'vitals', ['id'], unique=False)
