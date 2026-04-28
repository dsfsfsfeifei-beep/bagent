from pathlib import Path

from langchain_core.tools import tool

_DOC_PATH = Path(__file__).resolve().parents[2] / "docs" / "field_mapping.md"


def load_mapping_doc() -> str:
    if not _DOC_PATH.exists():
        return "(field_mapping.md not found)"
    return _DOC_PATH.read_text(encoding="utf-8")


@tool
def get_field_mapping(query: str = "") -> str:
    """返回 eBuy/SRM → 中台 → FOL 的字段映射规则文档。
    用于：用户问"X 字段在 FOL 叫什么 / 中台的 Y 来自哪里 / 这两个系统的字段怎么对应"。
    参数 query 目前未使用，整篇文档会被返回；后续若文档变大可在此处加关键字过滤。
    """
    return load_mapping_doc()
