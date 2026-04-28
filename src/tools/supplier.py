from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from ..auth import get_user_token
from ..settings import settings
from ._http import authed_get


@tool
def get_supplier(code: str, config: RunnableConfig) -> dict:
    """按供应商编码（supplier code）从中台查询供应商基础信息（名称、统一社会信用代码、状态、注册地等）。
    用于：用户问"供应商 XXX 是什么 / 它的基本信息 / 它的状态"等。
    参数 code 必须是精确的供应商编码，模糊查询请用 search_suppliers。
    """
    token = get_user_token(config)
    return authed_get(settings.middle_base_url, f"/api/suppliers/{code}", token)


@tool
def search_suppliers(keyword: str, limit: int = 10, config: RunnableConfig = None) -> list[dict]:
    """按名称/关键字在中台模糊搜索供应商，返回候选列表。
    用于：用户没给精确编码，只说了名字片段时。
    """
    token = get_user_token(config)
    return authed_get(
        settings.middle_base_url,
        "/api/suppliers/search",
        token,
        params={"q": keyword, "limit": limit},
    )
