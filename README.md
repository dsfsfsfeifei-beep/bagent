# bagent

供应商信息助手 —— 基于 LangChain + LangGraph，包装 `cloud-longsys-srm` 的 REST 接口为 tool，回答两类问题：

1. 供应商主数据查询（MDM）
2. 信息从 SRM/EBUY → 中台 → FOL 的流转追踪（接口报文日志 + 字段映射），并能一键重推 FOL

## 架构

- **LLM**：本地 Ollama（OpenAI 兼容端点 `http://localhost:11434/v1`），默认模型 `qwen3.6:35b`，需支持 tool calling
- **Agent**：`langgraph.prebuilt.create_react_agent`
- **记忆**：`SqliteSaver` checkpointer，按 `thread_id` 隔离（推荐 `user_<uid>`）
- **后端**：所有 tool 调向 `cloud-longsys-srm`（单一 `SRM_BASE_URL`）
- **鉴权**：用户 token 当作 `sid`，作为 URL 查询参数传给后端
- **字段映射**：写在 `docs/field_mapping.md`，由 `get_field_mapping` tool 返回
- **完整接口文档**：[docs/api.md](docs/api.md)

## 工具

数据查询：

| 名称 | 后端接口 |
| --- | --- |
| `search_suppliers(keyword)` | `POST /supplier-mdm/v1/querySupplierMdmList` |
| `get_supplier_by_number(supplier_number)` | 同上（按精确编码取一行，返回 id） |
| `get_supplier_detail(id)` | `POST /supplier-mdm/v1/querySupplierMdmDetail` |
| `query_interface_logs(...)` | `POST /interface-log/v1/queryPage` |
| `get_interface_log_detail(id)` | `GET /interface-log/v1/detail/{id}` |
| `get_field_mapping()` | 读 `docs/field_mapping.md` |

不可逆动作（agent 必须先 `confirm_with_user`）：

| 名称 | 后端接口 |
| --- | --- |
| `push_supplier_to_fol(supplier_number)` | `POST /supplier/v1/pushSupplierToFol` |

页面操作（仅 WebSocket 入口可用，需前端 SDK 配合）：

| 名称 | 用途 |
| --- | --- |
| `navigate_to(path)` | 路由跳转 |
| `open_supplier_detail(code)` | 打开供应商详情视图 |
| `highlight_element(selector)` | 高亮指引 |
| `prefill_form(form_id, data)` | 表单预填（不替用户提交） |
| `confirm_with_user(prompt)` | UI 确认框，返回用户选择 |

## 运行

```bash
# 1. 起 Ollama 并拉模型
ollama serve
ollama pull qwen3.6:35b

# 2. 起 agent
uv sync
cp .env.example .env    # 填 LLM_* 和 SRM_BASE_URL
uv run uvicorn src.server:app --reload --port 8080
```

两个入口：

**HTTP（无 UI 操作能力，纯问答）**

```bash
curl -X POST http://localhost:8080/chat \
  -H "Authorization: Bearer <sid>" \
  -H "Content-Type: application/json" \
  -d '{"message":"SUP001 为什么没推到 FOL","thread_id":"user_123"}'
```

**WebSocket（支持 UI tool 操作用户当前页面）**

`ws://localhost:8080/ws/<thread_id>`，子协议带 `bearer.<sid>`。前端接线见 [web/README.md](web/README.md)。

> Bearer 后面跟的 `<sid>` 就是后端 CAS 颁发的 session id。bagent 不解析它，仅在调 SRM 时作为 `?sid=` 透传。

## 典型对话

> "SUP001 为什么没推到 FOL"

agent 会按这个流程走：

1. `query_interface_logs(business_no="SUP001", target_system="FOL", success_flag="N")` → 拿到失败行 + `traceNo`
2. `query_interface_logs(trace_no=...)` → 看完整链路
3. 定位到具体阶段（`SUPPLIER_FOL_TOKEN` / `SUPPLIER_FOL_PUSH`），必要时 `get_interface_log_detail(log_id)` 看报文
4. 给出原因 + 建议（包括"是否要现在重推"，重推前会 `confirm_with_user`）

## 后续

- 字段映射文档变大后，`get_field_mapping` 改成关键字 RAG
- `SqliteSaver` → `PostgresSaver` 做生产持久化
- 加契约测试针对真实测试环境定时跑
