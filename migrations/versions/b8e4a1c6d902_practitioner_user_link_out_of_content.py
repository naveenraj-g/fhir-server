"""practitioner: keep the end-user link out of `content`

Revision ID: b8e4a1c6d902
Revises: a7d3f19c2b64
Create Date: 2026-11-18 15:00:00.000000

a7d3f19c2b64 carried the old `practitioner.user_id` into `content` as the
https://fhir-server.dev/fhir/StructureDefinition/user-id extension. The link
between a practitioner and its IAM user is not a FHIR element, so it now
lives only in the `practitioner.user_id` column (set through
PUT /practitioners/{id}/user), and the extension is no longer part of the
resource.

upgrade: remove that extension from every `content` (dropping the `extension`
key when it becomes empty). The `user_id` column is untouched, so no link is
lost.

downgrade: put the extension back for every row that has a `user_id`.
"""
import json
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'b8e4a1c6d902'
down_revision: Union[str, None] = 'a7d3f19c2b64'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

USER_ID_EXTENSION_URL = "https://fhir-server.dev/fhir/StructureDefinition/user-id"


def _json(value):
    return json.loads(value) if isinstance(value, str) else value


def upgrade() -> None:
    bind = op.get_bind()
    for row in bind.execute(sa.text("SELECT id, content FROM practitioner")).mappings().all():
        content = _json(row["content"])
        kept = [e for e in content.get("extension") or [] if e.get("url") != USER_ID_EXTENSION_URL]
        if len(kept) == len(content.get("extension") or []):
            continue
        if kept:
            content["extension"] = kept
        else:
            content.pop("extension", None)
        bind.execute(
            sa.text("UPDATE practitioner SET content = CAST(:c AS jsonb) WHERE id = :id"),
            {"c": json.dumps(content), "id": row["id"]},
        )


def downgrade() -> None:
    bind = op.get_bind()
    for row in bind.execute(
        sa.text("SELECT id, content, user_id FROM practitioner WHERE user_id IS NOT NULL")
    ).mappings().all():
        content = _json(row["content"])
        extensions = list(content.get("extension") or [])
        if any(e.get("url") == USER_ID_EXTENSION_URL for e in extensions):
            continue
        extensions.append({"url": USER_ID_EXTENSION_URL, "valueString": row["user_id"]})
        content["extension"] = extensions
        bind.execute(
            sa.text("UPDATE practitioner SET content = CAST(:c AS jsonb) WHERE id = :id"),
            {"c": json.dumps(content), "id": row["id"]},
        )
