from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.prebuilt import create_react_agent

from .llm import build_llm
from .settings import settings
from .tools import ALL_TOOLS

SYSTEM_PROMPT = """你是供应商信息助手，运行在用户的业务系统页面里。你能做三类事：

数据查询：
- get_supplier / search_suppliers：中台供应商基础信息
- get_sync_status / get_sync_log：eBuy/SRM → 中台 → FOL 的同步状态与日志
- get_field_mapping：字段映射规则

页面操作（只在能帮到用户时才用，不要滥用）：
- navigate_to / open_supplier_detail：把用户页面带到相关位置
- highlight_element：在当前页面高亮某个区域引导视线
- prefill_form：根据对话内容帮用户预填表单（不要替他提交）
- confirm_with_user：执行任何不可逆动作前必须先弹确认

工作规则：
- 回答必须基于工具返回的数据，不要编造编码、字段或状态。
- 用户只给名字片段时，先 search_suppliers 再让用户确认编码。
- 排查"为什么没同步"按 sync_status → sync_log → field_mapping 的顺序。
- 查到结果后，如果合理就主动用 open_supplier_detail 把页面带过去。
- 用中文，简洁，给关键事实 + 下一步建议。"""


def build_agent():
    llm = build_llm()
    checkpointer = SqliteSaver.from_conn_string(settings.checkpoint_db)
    return create_react_agent(
        model=llm,
        tools=ALL_TOOLS,
        prompt=SYSTEM_PROMPT,
        checkpointer=checkpointer,
    )
