"""响应模型集中地。接口字段一旦变化，只在这里改。

约定：
- 字段名按"中台规范化"后的名字命名（snake_case）。
- 上游接口字段名不一致时，用 Field(alias=...) 映射，不要在 tool 里手工搬字段。
- 多了无关字段不会报错（默认 ignore）；少了必填字段会 fail fast，比悄悄给 LLM 错数据好。
"""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

SourceSystem = Literal["ebuy", "srm"]
TargetSystem = Literal["middle", "fol"]


class _Base(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")


class Supplier(_Base):
    code: str = Field(alias="supplier_code")
    name: str = Field(alias="supplier_name")
    status: str
    source_system: SourceSystem | None = None
    unified_credit_code: str | None = None
    registered_address: str | None = None


class SupplierBrief(_Base):
    code: str = Field(alias="supplier_code")
    name: str = Field(alias="supplier_name")


class SyncStatus(_Base):
    supplier_code: str
    target: TargetSystem
    synced: bool
    last_synced_at: datetime | None = None
    current_version: str | None = None
    source_system: SourceSystem | None = None
    has_pending_failure: bool = False


class SyncLogEntry(_Base):
    supplier_code: str
    source: SourceSystem
    target: TargetSystem
    occurred_at: datetime
    status: Literal["success", "failed", "retrying"]
    message: str | None = None
    diff: dict | None = None
