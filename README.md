# bagent

供应商信息助手 —— 基于 LangChain + LangGraph，封装中台 / eBuy / SRM / FOL 的 REST 接口为 tool，回答两类问题：

1. 供应商基础信息查询（来自中台）
2. 信息从 eBuy/SRM → 中台 → FOL 的传递过程追踪（同步状态、日志、字段映射）

## 架构

- LLM：本地 Ollama（OpenAI 兼容端点 `http://localhost:11434/v1`），默认模型 `qwen3.6:35b`，需支持 tool calling
- Agent：`langgraph.prebuilt.create_react_agent`（ReAct + tool calling）
- 记忆：`SqliteSaver` checkpointer，按 `thread_id` 隔离（推荐用 `user_id`）
- 鉴权：每用户独立 token，从 HTTP `Authorization: Bearer ...` 取出，通过 `RunnableConfig.configurable.user_token` 透传给 tool
- 字段映射：写在 `docs/field_mapping.md`，由 `get_field_mapping` tool 返回

## 工具

数据查询：

| 名称 | 用途 |
| --- | --- |
| `get_supplier(code)` | 中台精确查询 |
| `search_suppliers(keyword)` | 中台模糊搜索 |
| `get_sync_status(supplier_code, target)` | 中台 / FOL 当前同步状态 |
| `get_sync_log(supplier_code, source, target)` | 同步日志，排查失败 |
| `get_field_mapping()` | 返回字段映射文档 |

页面操作（仅 WebSocket 入口可用，需前端 SDK 配合）：

| 名称 | 用途 |
| --- | --- |
| `navigate_to(path)` | 路由跳转 |
| `open_supplier_detail(code)` | 打开供应商详情视图 |
| `highlight_element(selector)` | 高亮指引 |
| `prefill_form(form_id, data)` | 表单预填（不提交） |
| `confirm_with_user(prompt)` | UI 确认框，返回用户选择 |

## 运行

```bash
# 1. 起 Ollama 并拉模型
ollama serve            # 后台跑
ollama pull qwen3.6:35b # 或你 ollama list 里实际的 tag

# 2. 起 agent
uv sync
cp .env.example .env    # 默认指向 localhost:11434，按需改 base_url
uv run uvicorn src.server:app --reload --port 8080
```

两个入口：

**HTTP（无 UI 操作能力，纯问答）**

```bash
curl -X POST http://localhost:8080/chat \
  -H "Authorization: Bearer <user_token>" \
  -H "Content-Type: application/json" \
  -d '{"message":"查供应商 SUP001 的同步状态","thread_id":"user_123"}'
```

**WebSocket（支持 UI tool 操作用户当前页面）**

`ws://localhost:8080/ws/<thread_id>`，子协议带 `bearer.<token>`。前端接线见 [web/README.md](web/README.md)。

## 后续

- 字段映射文档变大后，把 `get_field_mapping` 改为基于关键字的 RAG
- 接口稳定后用 OpenAPI spec 校验 tool 参数
- `SqliteSaver` 换 `PostgresSaver` 做生产持久化
