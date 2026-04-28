# 字段映射规则（占位）

> 把真实的 eBuy/SRM → 中台 → FOL 字段映射规则贴到这里。Agent 的 `get_field_mapping` 工具会原样读取并返回给模型。

## eBuy → 中台

| eBuy 字段 | 中台字段 | 说明 |
| --- | --- | --- |
| supplierCode | supplier_code | 主键，必填 |
| supplierName | supplier_name | |

## SRM → 中台

| SRM 字段 | 中台字段 | 说明 |
| --- | --- | --- |
| vendorId | supplier_code | 来源系统区分通过 source_system 字段 |
| vendorName | supplier_name | |

## 中台 → FOL

| 中台字段 | FOL 字段 | 说明 |
| --- | --- | --- |
| supplier_code | folSupplierId | |
| supplier_name | folSupplierName | |
| status | folStatus | 中台 ACTIVE → FOL 1，其他 → 0 |
