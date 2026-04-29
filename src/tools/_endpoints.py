"""cloud-longsys-srm 接口路径常量。接口路径变化只改这一处。
所有接口都挂在 SRM_BASE_URL 上，鉴权走 ?sid=<token>。
"""

# 供应商主数据
SUPPLIER_SYNC_MASTER_DATA = "/supplier/v1/syncSupplierMasterData"      # SRM/EBUY 推主数据进来
SUPPLIER_SYNC_SRM_LIST = "/supplier/v1/syncSRMSupplierInfoList"        # 按编码查 SRM 侧主数据

SUPPLIER_MDM_LIST = "/supplier-mdm/v1/querySupplierMdmList"            # MDM 列表（分页 + 多条件）
SUPPLIER_MDM_DETAIL = "/supplier-mdm/v1/querySupplierMdmDetail"        # MDM 详情（按 id）

# FOL
SUPPLIER_PUSH_FOL = "/supplier/v1/pushSupplierToFol"

# 接口报文日志
INTERFACE_LOG_PAGE = "/interface-log/v1/queryPage"
INTERFACE_LOG_DETAIL = "/interface-log/v1/detail/{id}"
