"""add batch 5 reference identifier fallback columns

Revision ID: 9e244ee31e3b
Revises: 5933b68ebf9b
Create Date: 2026-11-01 20:47:15.925299

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '9e244ee31e3b'
down_revision: Union[str, None] = '5933b68ebf9b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # medication_request_note
    op.add_column('medication_request_note', sa.Column('author_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True))
    op.add_column('medication_request_note', sa.Column('author_identifier_type_system', sa.String(), nullable=True))
    op.add_column('medication_request_note', sa.Column('author_identifier_type_version', sa.String(), nullable=True))
    op.add_column('medication_request_note', sa.Column('author_identifier_type_code', sa.String(), nullable=True))
    op.add_column('medication_request_note', sa.Column('author_identifier_type_display', sa.String(), nullable=True))
    op.add_column('medication_request_note', sa.Column('author_identifier_type_user_selected', sa.Boolean(), nullable=True))
    op.add_column('medication_request_note', sa.Column('author_identifier_type_text', sa.String(), nullable=True))
    op.add_column('medication_request_note', sa.Column('author_identifier_system', sa.String(), nullable=True))
    op.add_column('medication_request_note', sa.Column('author_identifier_value', sa.String(), nullable=True))
    op.add_column('medication_request_note', sa.Column('author_identifier_period_start', sa.DateTime(timezone=True), nullable=True))
    op.add_column('medication_request_note', sa.Column('author_identifier_period_end', sa.DateTime(timezone=True), nullable=True))

    # questionnaire_response_answer
    op.add_column('questionnaire_response_answer', sa.Column('value_reference_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True))
    op.add_column('questionnaire_response_answer', sa.Column('value_reference_identifier_type_system', sa.String(), nullable=True))
    op.add_column('questionnaire_response_answer', sa.Column('value_reference_identifier_type_version', sa.String(), nullable=True))
    op.add_column('questionnaire_response_answer', sa.Column('value_reference_identifier_type_code', sa.String(), nullable=True))
    op.add_column('questionnaire_response_answer', sa.Column('value_reference_identifier_type_display', sa.String(), nullable=True))
    op.add_column('questionnaire_response_answer', sa.Column('value_reference_identifier_type_user_selected', sa.Boolean(), nullable=True))
    op.add_column('questionnaire_response_answer', sa.Column('value_reference_identifier_type_text', sa.String(), nullable=True))
    op.add_column('questionnaire_response_answer', sa.Column('value_reference_identifier_system', sa.String(), nullable=True))
    op.add_column('questionnaire_response_answer', sa.Column('value_reference_identifier_value', sa.String(), nullable=True))
    op.add_column('questionnaire_response_answer', sa.Column('value_reference_identifier_period_start', sa.DateTime(timezone=True), nullable=True))
    op.add_column('questionnaire_response_answer', sa.Column('value_reference_identifier_period_end', sa.DateTime(timezone=True), nullable=True))

    # service_request_note
    op.add_column('service_request_note', sa.Column('author_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True))
    op.add_column('service_request_note', sa.Column('author_identifier_type_system', sa.String(), nullable=True))
    op.add_column('service_request_note', sa.Column('author_identifier_type_version', sa.String(), nullable=True))
    op.add_column('service_request_note', sa.Column('author_identifier_type_code', sa.String(), nullable=True))
    op.add_column('service_request_note', sa.Column('author_identifier_type_display', sa.String(), nullable=True))
    op.add_column('service_request_note', sa.Column('author_identifier_type_user_selected', sa.Boolean(), nullable=True))
    op.add_column('service_request_note', sa.Column('author_identifier_type_text', sa.String(), nullable=True))
    op.add_column('service_request_note', sa.Column('author_identifier_system', sa.String(), nullable=True))
    op.add_column('service_request_note', sa.Column('author_identifier_value', sa.String(), nullable=True))
    op.add_column('service_request_note', sa.Column('author_identifier_period_start', sa.DateTime(timezone=True), nullable=True))
    op.add_column('service_request_note', sa.Column('author_identifier_period_end', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    # service_request_note
    op.drop_column('service_request_note', 'author_identifier_period_end')
    op.drop_column('service_request_note', 'author_identifier_period_start')
    op.drop_column('service_request_note', 'author_identifier_value')
    op.drop_column('service_request_note', 'author_identifier_system')
    op.drop_column('service_request_note', 'author_identifier_type_text')
    op.drop_column('service_request_note', 'author_identifier_type_user_selected')
    op.drop_column('service_request_note', 'author_identifier_type_display')
    op.drop_column('service_request_note', 'author_identifier_type_code')
    op.drop_column('service_request_note', 'author_identifier_type_version')
    op.drop_column('service_request_note', 'author_identifier_type_system')
    op.drop_column('service_request_note', 'author_identifier_use')

    # questionnaire_response_answer
    op.drop_column('questionnaire_response_answer', 'value_reference_identifier_period_end')
    op.drop_column('questionnaire_response_answer', 'value_reference_identifier_period_start')
    op.drop_column('questionnaire_response_answer', 'value_reference_identifier_value')
    op.drop_column('questionnaire_response_answer', 'value_reference_identifier_system')
    op.drop_column('questionnaire_response_answer', 'value_reference_identifier_type_text')
    op.drop_column('questionnaire_response_answer', 'value_reference_identifier_type_user_selected')
    op.drop_column('questionnaire_response_answer', 'value_reference_identifier_type_display')
    op.drop_column('questionnaire_response_answer', 'value_reference_identifier_type_code')
    op.drop_column('questionnaire_response_answer', 'value_reference_identifier_type_version')
    op.drop_column('questionnaire_response_answer', 'value_reference_identifier_type_system')
    op.drop_column('questionnaire_response_answer', 'value_reference_identifier_use')

    # medication_request_note
    op.drop_column('medication_request_note', 'author_identifier_period_end')
    op.drop_column('medication_request_note', 'author_identifier_period_start')
    op.drop_column('medication_request_note', 'author_identifier_value')
    op.drop_column('medication_request_note', 'author_identifier_system')
    op.drop_column('medication_request_note', 'author_identifier_type_text')
    op.drop_column('medication_request_note', 'author_identifier_type_user_selected')
    op.drop_column('medication_request_note', 'author_identifier_type_display')
    op.drop_column('medication_request_note', 'author_identifier_type_code')
    op.drop_column('medication_request_note', 'author_identifier_type_version')
    op.drop_column('medication_request_note', 'author_identifier_type_system')
    op.drop_column('medication_request_note', 'author_identifier_use')
