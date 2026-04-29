from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from ..auth import get_user_token
from ..schemas import SupplierMdmDetail, SupplierMdmPage
from ._endpoints import SUPPLIER_MDM_DETAIL, SUPPLIER_MDM_LIST
from ._http import srm_post


@tool
def search_suppliers(
    keyword: str,
    size: int = 10,
    config: RunnableConfig = None,
) -> dict:
    """按关键字（供应商编码 / 名称 / 统一社会信用代码）在 MDM 里分页搜索供应商。
    用于：用户没给精确编码，只说了名字片段或部分编码。
    返回 SupplierMdmPage：records[] 含 id/supplier_number/supplier_name/supplier_status/sync_status，total 等分页字段。
    """
    sid = get_user_token(config)
    raw = srm_post(
        SUPPLIER_MDM_LIST,
        sid,
        body={"current": 1, "size": size, "keyword": keyword},
    )
    return SupplierMdmPage.model_validate(raw).model_dump(mode="json")


@tool
def get_supplier_by_number(
    supplier_number: str,
    config: RunnableConfig,
) -> dict | None:
    """按精确供应商编码在 MDM 列表接口里取一条，返回列表行（含 id 等概览字段）；找不到返回 null。
    用于：已知编码，先拿到 id 再决定是否调 get_supplier_detail。
    """
    sid = get_user_token(config)
    raw = srm_post(
        SUPPLIER_MDM_LIST,
        sid,
        body={"current": 1, "size": 1, "supplierNumber": supplier_number},
    )
    page = SupplierMdmPage.model_validate(raw)
    if not page.records:
        return None
    return page.records[0].model_dump(mode="json")


@tool
def get_supplier_detail(supplier_id: int, config: RunnableConfig) -> dict:
    """按 MDM 头表 id 查供应商完整详情（含分类/银行/联系人/地址/地点/发货地等子表）。
    用于：用户问"详细信息 / 银行账号 / 联系人 / 注册地"等深度问题。
    取 id 的方式：先 search_suppliers 或 get_supplier_by_number 拿到 records[0].id。
    """
    sid = get_user_token(config)
    raw = srm_post(SUPPLIER_MDM_DETAIL, sid, body={"id": supplier_id})
    return SupplierMdmDetail.model_validate(raw).model_dump(mode="json")
