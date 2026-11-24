"""TaskModel row -> FHIR R4 Task. The only
read-side mapper.

The resource is stored whole in TaskModel.content (see the
model's docstring), so this doesn't rebuild anything from columns — see
app.fhir.mappers.content.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.mappers.content import content_resource

if TYPE_CHECKING:
    from app.models.task import TaskModel


def to_fhir_task(task: TaskModel) -> dict:
    return content_resource("Task", task.task_id, task)
