from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SourceContent(BaseModel):
    """来源正文数据模型。正文按内容去重且不可更新，不参与业务软删除。"""

    id: Optional[int] = Field(default=None, ge=1)
    content_hash: str = Field(min_length=64, max_length=64)
    content: str
    create_time: Optional[datetime] = None
