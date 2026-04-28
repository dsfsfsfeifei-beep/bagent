# bagent

供应商信息助手 —— 基于 LangChain + LangGraph，封装中台 / eBuy / SRM / FOL 的 REST 接口为 tool，回答两类问题：

1. 供应商基础信息查询（来自中台）
2. 信息从 eBuy/SRM → 中台 → FOL 的传递过程追踪（同步状态、日志、字段映射）

## 架构

- LLM：公司内部 OpenAI 兼容接口（`langchain-openai`）
- Agent：`langgraph.prebuilt.create_react_agent`（ReAct + tool calling）
- 记忆：`SqliteSaver` checkpointer，按 `thread_id` 隔离（推荐用 `user_id`）
- 鉴权：每用户独立 token，从 HTTP `Authorization: Bearer ...` 取出，通过 `RunnableConfig.configurable.user_token` 透传给 tool
- 字段映射：写在 `docs/field_mapping.md`，由 `get_field_mapping` tool 返回

## 工具

| 名称 | 用途 |
| --- | --- |
| `get_supplier(code)` | 中台精确查询 |
| `search_suppliers(keyword)` | 中台模糊搜索 |
| `get_sync_status(supplier_code, target)` | 中台 / FOL 当前同步状态 |
| `get_sync_log(supplier_code, source, target)` | 同步日志，排查失败 |
| `get_field_mapping()` | 返回字段映射文档 |

## 运行

```bash
uv sync
cp .env.example .env  # 填好 LLM 和各系统 base_url
uv run uvicorn src.server:app --reload --port 8080
```

调用：

```bash
curl -X POST http://localhost:8080/chat \
  -H "Authorization: Bearer <user_token>" \
  -H "Content-Type: application/json" \
  -d '{"message":"查供应商 SUP001 的同步状态","thread_id":"user_123"}'
```

## 后续

- 字段映射文档变大后，把 `get_field_mapping` 改为基于关键字的 RAG
- 接口稳定后用 OpenAPI spec 校验 tool 参数
- `SqliteSaver` 换 `PostgresSaver` 做生产持久化
