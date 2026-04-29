# cloud-longsys-srm 接口梳理

来源：`D:\workspace\longsys\mdm-srm\cloud-longsys-srm` 分支 `develop_guozhu.huang`。

## 通用约定

- **服务**：所有接口都挂在同一个 SRM 服务上（不要按业务拆 base_url）。
- **鉴权**：URL 查询参数 `?sid=<token>`。
- **响应包装**：`RespMsg{ code, msg, data }`，`code == "0"` 为成功，否则 `msg` 是错误描述。
- **时间格式**：`yyyy-MM-dd HH:mm:ss`（GMT+8）。
- **字段命名**：请求/响应 body 全部 camelCase（Pydantic 侧做了 alias 映射）。

## 1. 推送供应商主数据

### 1.1 同步主数据 SRM/EBUY → 中台
`POST /supplier/v1/syncSupplierMasterData`

Body：`SupplierMasterDataDto`，关键字段
- `data: SupplierInfoVo[]` —— 主数据列表，每行包含：
  - `supplierNumber` *（关键）*、`supplierName`、`supplierStatus`、`supplierUSCI`、`erpVendorId`
  - `supplierCategoryVos[]` / `supplierBankVos[]` / `supplierContactVos[]` / `supplierAddressVos[]` / `supplierSiteVos[]` / `supplierShipFromVos[]`
- 顶层 `uid` / `busSystem` 可选

返回与请求同结构，单行带 `success` / `errMsg`。单条失败不阻断整批。

### 1.2 按编码反查 SRM 主数据
`POST /supplier/v1/syncSRMSupplierInfoList`

Body：`SupplierInfoDto`
- `supplierNumbers: string[]`
- `uid` / `busSystem` / `lang`

返回 `SupplierMasterDataDto`。

### 1.3 MDM 列表（分页 + 多条件）
`POST /supplier-mdm/v1/querySupplierMdmList`

Body：`SupplierMdmHeaderPageDto`
- `current` / `size` *（必填）*
- `keyword`（编码/名称/统一社会信用代码模糊匹配）
- `supplierNumber` / `supplierName` / `supplierStatus` / `syncStatus`
- `creationDateStart` / `creationDateEnd`

返回分页：`records[]` 含 `id` / `traceNo` / `supplierNumber` / `supplierName` / `supplierStatus` / `syncStatus` / `erpVendorId` / `creationDate`。

### 1.4 MDM 详情
`POST /supplier-mdm/v1/querySupplierMdmDetail`

Body：`{ id: long }`，返回完整字段（含所有子表）。

## 2. 推送 FOL

`POST /supplier/v1/pushSupplierToFol`

Body：`{ supplierNumber: string }` *（@NotEmpty）*

返回 `FolSupplierPushResultVo`：`supplierId` / `supplierNumber` / `supplierName` / `pushStatus` / `errorMessage` / `foLTokenResult` / `folSupplierPushResponse`。

内部流程：查 SRM → 取 FOL token → 推送 FOL，每一步都写日志（`stageType` 见下）。

## 3. 接口报文日志

### 3.1 分页查询
`POST /interface-log/v1/queryPage`

Body：`InterfaceInfoLogPageDto`
- `current` / `size` *（必填）*
- `businessNo`（业务编码，通常是 `supplierNumber`）
- `traceNo`（链路流水号，串起一次完整调用的所有阶段）
- `interfaceType`（如 `SUPPLIER_MDM`）
- `stageType`：
  - `SUPPLIER_INBOUND_REQUEST` —— SRM/EBUY 推主数据进中台
  - `SUPPLIER_FOL_TOKEN` —— 获取 FOL token
  - `SUPPLIER_FOL_PUSH` —— 推送 FOL
- `targetSystem`：`SRM` / `FOL` / `MDM`
- `successFlag`：`Y` / `N`
- `creationDateStart` / `creationDateEnd`

返回分页 `records[]`，**不含 `requestBody` / `responseBody`**，要看报文走详情接口。

### 3.2 详情
`GET /interface-log/v1/detail/{id}`

返回单条完整记录，含 `requestBody` / `responseBody` 字符串。

## bagent 工具映射

| 工具 | 后端接口 |
| --- | --- |
| `search_suppliers(keyword)` | `POST /supplier-mdm/v1/querySupplierMdmList` (with `keyword`) |
| `get_supplier_by_number(supplier_number)` | `POST /supplier-mdm/v1/querySupplierMdmList` (with `supplierNumber`, size=1) |
| `get_supplier_detail(id)` | `POST /supplier-mdm/v1/querySupplierMdmDetail` |
| `query_interface_logs(...)` | `POST /interface-log/v1/queryPage` |
| `get_interface_log_detail(id)` | `GET /interface-log/v1/detail/{id}` |
| `push_supplier_to_fol(supplier_number)` | `POST /supplier/v1/pushSupplierToFol`（不可逆，调用前 confirm_with_user） |

`syncSupplierMasterData` / `syncSRMSupplierInfoList` 是 SRM/EBUY 主动调中台用的，bagent 暂不直接用。
