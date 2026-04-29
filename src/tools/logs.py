"""接口报文日志查询。
SRM 把 SRM/EBUY → MDM、MDM → FOL 每一步调用都写到 InterfaceInfoLog。
排查"为什么没同步过去"的第一现场就是这两个接口。
"""
from typing import Literal

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from ..auth import get_user_token
from ..schemas import InterfaceLogDetail, InterfaceLogPage
from ._endpoints import INTERFACE_LOG_DETAIL, INTERFACE_LOG_PAGE
from ._http import srm_get, srm_post


@tool
def query_interface_logs(
    business_no: str | None = None,
    trace_no: str | None = None,
    interface_type: str | None = None,
    stage_type: str | None = None,
    target_system: Literal["SRM", "FOL", "MDM", None] = None,
    success_flag: Literal["Y", "N", None] = None,
    size: int = 20,
    config: RunnableConfig = None,
) -> dict:
    """分页查询接口报文日志，返回 InterfaceLogPage（不含 request/response 报文，要看报文调 get_interface_log_detail）。

    常用过滤：
    - business_no：业务编码（通常是 supplier_number）
    - trace_no：调用链路流水号，串起一次完整调用的所有阶段
    - interface_type：常见值 "SUPPLIER_MDM"
    - stage_type：常见值 "SUPPLIER_INBOUND_REQUEST"（SRM/EBUY → 中台）、"SUPPLIER_FOL_TOKEN"（取 FOL token）、"SUPPLIER_FOL_PUSH"（推 FOL）
    - target_system："SRM" / "FOL" / "MDM"
    - success_flag："Y" / "N"

    排查思路：
    1. 用户问"X 没传到 FOL" → business_no=X, target_system="FOL", success_flag="N"
    2. 找到失败行后，用 trace_no 把同链路的所有阶段拉出来看流转
    3. 想看具体报文 → get_interface_log_detail(id)
    """
    sid = get_user_token(config)
    body: dict = {"current": 1, "size": size}
    if business_no:
        body["businessNo"] = business_no
    if trace_no:
        body["traceNo"] = trace_no
    if interface_type:
        body["interfaceType"] = interface_type
    if stage_type:
        body["stageType"] = stage_type
    if target_system:
        body["targetSystem"] = target_system
    if success_flag:
        body["successFlag"] = success_flag

    raw = srm_post(INTERFACE_LOG_PAGE, sid, body=body)
    return InterfaceLogPage.model_validate(raw).model_dump(mode="json")


@tool
def get_interface_log_detail(log_id: int, config: RunnableConfig) -> dict:
    """按日志 id 查完整详情，含 request_body / response_body 字符串报文。
    用于：从 query_interface_logs 拿到失败行后，看具体的请求/响应内容定位原因。
    """
    sid = get_user_token(config)
    raw = srm_get(INTERFACE_LOG_DETAIL.format(id=log_id), sid)
    return InterfaceLogDetail.model_validate(raw).model_dump(mode="json")
