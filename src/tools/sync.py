from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from pydantic import TypeAdapter

from ..auth import get_user_token
from ..schemas import SourceSystem, SyncLogEntry, SyncStatus, TargetSystem
from ..settings import settings
from ._endpoints import FOL_SYNC_STATUS, MIDDLE_SYNC_LOGS, MIDDLE_SYNC_STATUS
from ._http import authed_get

_SyncLogList = TypeAdapter(list[SyncLogEntry])


@tool
def get_sync_status(
    supplier_code: str,
    target: TargetSystem,
    config: RunnableConfig,
) -> dict:
    """查询某个供应商在目标系统（中台 middle 或 FOL）当前的同步状态。
    返回字段：是否已同步、最近同步时间、当前版本、上游来源系统（ebuy/srm）、是否有挂起的失败。
    用于：用户问"这个供应商同步到 FOL 了吗 / 中台有没有这个供应商 / 为什么 FOL 看不到"。
    """
    token = get_user_token(config)
    if target == "middle":
        base, path = settings.middle_base_url, MIDDLE_SYNC_STATUS
    else:
        base, path = settings.fol_base_url, FOL_SYNC_STATUS
    raw = authed_get(base, path.format(code=supplier_code), token)
    return SyncStatus.model_validate(raw).model_dump(mode="json")


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
    raw = authed_get(
        settings.middle_base_url,
        MIDDLE_SYNC_LOGS,
        token,
        params={
            "supplier_code": supplier_code,
            "source": source,
            "target": target,
            "limit": limit,
        },
    )
    return [e.model_dump(mode="json") for e in _SyncLogList.validate_python(raw)]
