from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.prebuilt import create_react_agent

from .llm import build_llm
from .settings import settings
from .tools import ALL_TOOLS

SYSTEM_PROMPT = """你是供应商信息助手。你能做两件事：
1. 通过中台接口查询供应商基础信息（精确编码用 get_supplier，模糊关键字用 search_suppliers）。
2. 追踪信息从 eBuy/SRM 流转到中台再到 FOL 的过程：用 get_sync_status 看当前状态，用 get_sync_log 查具体日志，用 get_field_mapping 查字段映射规则。

回答规则：
- 必须基于工具返回的数据，不要编造编码、字段或状态。
- 用户给的是名字而非编码时，先 search_suppliers 再让用户确认。
- 排查"为什么没同步"类问题时，按 sync_status → sync_log → field_mapping 的顺序逐步定位。
- 用中文回答，简洁、给关键事实和下一步建议。"""


def build_agent():
    llm = build_llm()
    checkpointer = SqliteSaver.from_conn_string(settings.checkpoint_db)
    return create_react_agent(
        model=llm,
        tools=ALL_TOOLS,
        prompt=SYSTEM_PROMPT,
        checkpointer=checkpointer,
    )
