from .fol import push_supplier_to_fol
from .logs import get_interface_log_detail, query_interface_logs
from .mapping import get_field_mapping
from .supplier import get_supplier_by_number, get_supplier_detail, search_suppliers
from .ui import (
    confirm_with_user,
    highlight_element,
    navigate_to,
    open_supplier_detail,
    prefill_form,
)

DATA_TOOLS = [
    search_suppliers,
    get_supplier_by_number,
    get_supplier_detail,
    query_interface_logs,
    get_interface_log_detail,
    get_field_mapping,
]

ACTION_TOOLS = [
    push_supplier_to_fol,
]

UI_TOOLS = [
    navigate_to,
    open_supplier_detail,
    highlight_element,
    prefill_form,
    confirm_with_user,
]

ALL_TOOLS = DATA_TOOLS + ACTION_TOOLS + UI_TOOLS
