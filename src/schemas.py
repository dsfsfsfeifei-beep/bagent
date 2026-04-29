"""响应模型集中地。后端字段是 camelCase，全部用 alias 映射，Python 侧用 snake_case。

变更原则：
- 上游字段重命名 → 改 alias，业务代码不动。
- 上游加无关字段 → 默认忽略（model_config extra="ignore"）。
- 必填字段缺失 → fail fast，不要把垃圾数据给 LLM。
"""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

TargetSystem = Literal["SRM", "FOL", "MDM"]
SuccessFlag = Literal["Y", "N"]


class _Base(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")


# ---- 供应商 ---------------------------------------------------------------
class SupplierMdmRow(_Base):
    """querySupplierMdmList 列表行。"""
    id: int
    trace_no: str | None = Field(default=None, alias="traceNo")
    supplier_number: str = Field(alias="supplierNumber")
    supplier_name: str | None = Field(default=None, alias="supplierName")
    supplier_status: str | None = Field(default=None, alias="supplierStatus")
    sync_status: str | None = Field(default=None, alias="syncStatus")
    erp_vendor_id: str | None = Field(default=None, alias="erpVendorId")
    creation_date: datetime | None = Field(default=None, alias="creationDate")


class SupplierMdmPage(_Base):
    records: list[SupplierMdmRow]
    total: int
    pages: int | None = None
    current: int
    size: int


class SupplierMdmDetail(_Base):
    """querySupplierMdmDetail 详情。仅暴露高价值字段，其它跟着 extra ignore 走。"""
    id: int
    supplier_number: str = Field(alias="supplierNumber")
    supplier_name: str | None = Field(default=None, alias="supplierName")
    supplier_name_en: str | None = Field(default=None, alias="supplierNameEn")
    supplier_status: str | None = Field(default=None, alias="supplierStatus")
    supplier_usci: str | None = Field(default=None, alias="supplierUSCI")
    supplier_duns: str | None = Field(default=None, alias="supplierDUNS")
    erp_vendor_id: str | None = Field(default=None, alias="erpVendorId")
    supplier_type: str | None = Field(default=None, alias="supplierType")
    supplier_level: str | None = Field(default=None, alias="supplierLevel")
    legal_representative: str | None = Field(default=None, alias="legalRepresentative")
    incorporation_date: datetime | None = Field(default=None, alias="incorporationDate")
    payment_term: str | None = Field(default=None, alias="paymentTerm")
    creation_time: datetime | None = Field(default=None, alias="creationTime")
    # 嵌套子表保留为原始 list[dict]，agent 直接看就行
    supplier_category_vos: list[dict] | None = Field(default=None, alias="supplierCategoryVos")
    supplier_bank_vos: list[dict] | None = Field(default=None, alias="supplierBankVos")
    supplier_contact_vos: list[dict] | None = Field(default=None, alias="supplierContactVos")
    supplier_address_vos: list[dict] | None = Field(default=None, alias="supplierAddressVos")
    supplier_site_vos: list[dict] | None = Field(default=None, alias="supplierSiteVos")
    supplier_ship_from_vos: list[dict] | None = Field(default=None, alias="supplierShipFromVos")


# ---- FOL 推送 -------------------------------------------------------------
class FolPushResult(_Base):
    supplier_id: str | None = Field(default=None, alias="supplierId")
    supplier_number: str | None = Field(default=None, alias="supplierNumber")
    supplier_name: str | None = Field(default=None, alias="supplierName")
    push_status: str | None = Field(default=None, alias="pushStatus")
    error_message: str | None = Field(default=None, alias="errorMessage")
    fol_token_result: dict | None = Field(default=None, alias="foLTokenResult")
    fol_supplier_push_response: dict | None = Field(default=None, alias="folSupplierPushResponse")


# ---- 接口日志 -------------------------------------------------------------
class InterfaceLogRow(_Base):
    id: int
    trace_no: str | None = Field(default=None, alias="traceNo")
    business_no: str | None = Field(default=None, alias="businessNo")
    interface_type: str | None = Field(default=None, alias="interfaceType")
    stage_type: str | None = Field(default=None, alias="stageType")
    target_system: str | None = Field(default=None, alias="targetSystem")
    request_url: str | None = Field(default=None, alias="requestUrl")
    http_method: str | None = Field(default=None, alias="httpMethod")
    success_flag: SuccessFlag | None = Field(default=None, alias="successFlag")
    error_msg: str | None = Field(default=None, alias="errorMsg")
    creation_date: datetime | None = Field(default=None, alias="creationDate")


class InterfaceLogPage(_Base):
    records: list[InterfaceLogRow]
    total: int
    pages: int | None = None
    current: int
    size: int


class InterfaceLogDetail(InterfaceLogRow):
    request_body: str | None = Field(default=None, alias="requestBody")
    response_body: str | None = Field(default=None, alias="responseBody")
