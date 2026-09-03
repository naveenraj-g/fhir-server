"""drop_invalid_practitioner_qualification_status

Practitioner.qualification.status doesn't exist in FHIR R4 — the spec only
defines identifier, code, period, and issuer under qualification (`status`
is an R5 addition). google-fhir-r4's R4 conformance oracle correctly
rejected mapper output carrying it. Table was empty (0 rows, none with
status populated) at the time of this migration, confirmed live before
dropping.

Revision ID: 0a0625d11afb
Revises: dd86c3fb5aa3
Create Date: 2026-09-03 17:59:06.479271

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = '0a0625d11afb'
down_revision: Union[str, None] = 'dd86c3fb5aa3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column('practitioner_qualification', 'status_code')
    op.drop_column('practitioner_qualification', 'status_display')
    op.drop_column('practitioner_qualification', 'status_text')
    op.drop_column('practitioner_qualification', 'status_system')


def downgrade() -> None:
    op.add_column('practitioner_qualification', sa.Column('status_system', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('practitioner_qualification', sa.Column('status_text', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('practitioner_qualification', sa.Column('status_display', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('practitioner_qualification', sa.Column('status_code', sa.VARCHAR(), autoincrement=False, nullable=True))
