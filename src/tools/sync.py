from typing import Literal

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from ..auth import get_user_token
from ..settings import settings
from ._http import authed_get

SourceSystem = Literal["ebuy", "srm"]
TargetSystem = Literal["middle", "fol"]


@tool
def get_sync_status(
    supplier_code: str,
    target: TargetSystem,
    config: RunnableConfig,
) -> dict:
    """查询某个供应商在目标系统（中台 middle 或 FOL）当前的同步状态。
    返回字段大致包含：是否已同步、最近同步时间、当前版本、上游来源系统（ebuy/srm）、是否有挂起的失败。
    用于：用户问"这个供应商同步到 FOL 了吗 / 中台有没有这个供应商 / 为什么 FOL 看不到"。
    """
    token = get_user_token(config)
    base = settings.middle_base_url if target == "middle" else settings.fol_base_url
    return authed_get(base, f"/api/sync-status/{supplier_code}", token)


@tool
def get_sync_log(
    supplier_code: str,
    source: SourceSystem,
    target: TargetSystem,
    limit: int = 20,
    config: RunnableConfig = None,
) -> list[dict]:
    """查询某供应商从 source（ebuy/srm）到 target（middle/fol）的同步日志（最近 N 条），用于排查失败原因、字段差异、重试记录。
    用于：用户问"为什么没传过去 / 同步失败原因 / 最近一次推送时间"。
    """
    token = get_user_token(config)
    return authed_get(
        settings.middle_base_url,
        "/api/sync-logs",
        token,
        params={
            "supplier_code": supplier_code,
            "source": source,
            "target": target,
            "limit": limit,
        },
    )
