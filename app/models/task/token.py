from sqlalchemy import BigInteger, Column, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base

# Search parameters held in TaskToken, and the Task element each reads (`performer` reads
# performerType, the recommended type of performer).
TOKEN_PARAMS = {
    "business-status": "businessStatus",
    "code": "code",
    "performer": "performerType",
}


class TaskToken(Base):
    """Search index for the three CodeableConcept token parameters (`business-status`, `code`,
    `performer`): one row per coding of each concept - a token search matches any coding of any
    entry - plus one code-less row for a concept with only `text`, so `:text` still finds it.
    `param` says which search parameter the row belongs to (see TOKEN_PARAMS). Derived from
    TaskModel.content - never read to build a response.

      <param>              -> system, code
      <param>:text         -> text_norm (CodeableConcept.text) / display_norm
      <param>:in/:below/.. -> system, code, resolved through the terminology service"""

    __tablename__ = "task_token"
    __table_args__ = (Index("ix_task_token_param_code", "param", "code"),)

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    task_pk = Column(BigInteger, ForeignKey("task.id"), nullable=False, index=True)
    param = Column(String, nullable=False)
    system = Column(String, nullable=True)
    code = Column(String, nullable=True)
    display_norm = Column(String, nullable=True)
    text_norm = Column(String, nullable=True)

    task = relationship("TaskModel", back_populates="tokens")
