"""UI tools —— 通过 WebSocket 让用户当前页面执行动作。

约定：
- 每个 tool 走 Session.call_ui()，前端必须实现同名 handler。
- 失败/超时会抛 UIError，被 LangGraph 捕获后作为 tool 错误回给 LLM，让模型自己决定下一步。
"""
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from ..auth import get_session


@tool
async def navigate_to(path: str, config: RunnableConfig) -> str:
    """让用户当前页面跳转到给定的应用内路径（如 "/suppliers/SUP001"）。
    用于：用户希望被带到某个页面，或为后续 UI 操作做准备。
    """
    await get_session(config).call_ui("navigate_to", {"path": path})
    return f"navigated to {path}"


@tool
async def open_supplier_detail(code: str, config: RunnableConfig) -> str:
    """在用户当前页面打开指定供应商的详情视图（路由由前端决定）。
    用于：用户问到某供应商后，主动把页面带过去。
    """
    await get_session(config).call_ui("open_supplier_detail", {"code": code})
    return f"opened supplier detail for {code}"


@tool
async def highlight_element(selector: str, config: RunnableConfig) -> str:
    """高亮当前页面中匹配 CSS selector 的元素，引导用户视线。
    selector 应尽量稳健（用 data-* 属性，不要用易变的类名/层级）。
    """
    await get_session(config).call_ui("highlight_element", {"selector": selector})
    return f"highlighted {selector}"


@tool
async def prefill_form(form_id: str, data: dict, config: RunnableConfig) -> str:
    """把 data 中的键值预填到前端 form_id 标识的表单里（不提交）。
    用于：根据用户对话内容帮他把表单填好，让他确认后自己提交。
    """
    await get_session(config).call_ui("prefill_form", {"form_id": form_id, "data": data})
    return f"prefilled form {form_id}"


@tool
async def confirm_with_user(prompt: str, config: RunnableConfig) -> str:
    """在 UI 上弹出一个确认框，等用户点"确认"或"取消"，把结果返回给 agent。
    用于：执行任何不可逆动作前必须调用，例如重推同步、删除、修改。
    返回 "confirmed" 或 "cancelled"。
    """
    result = await get_session(config).call_ui(
        "confirm_with_user", {"prompt": prompt}, timeout=120.0
    )
    return "confirmed" if result.get("confirmed") else "cancelled"
