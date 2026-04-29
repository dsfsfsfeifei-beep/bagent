from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from ..auth import get_user_token
from ..schemas import FolPushResult
from ._endpoints import SUPPLIER_PUSH_FOL
from ._http import srm_post


@tool
def push_supplier_to_fol(supplier_number: str, config: RunnableConfig) -> dict:
    """手工触发把指定供应商推送到 FOL。这是不可逆动作，调用前必须先 confirm_with_user 取得用户同意。
    返回 FolPushResult（push_status / error_message / fol_token_result / fol_supplier_push_response）。
    """
    sid = get_user_token(config)
    raw = srm_post(SUPPLIER_PUSH_FOL, sid, body={"supplierNumber": supplier_number})
    return FolPushResult.model_validate(raw).model_dump(mode="json")
