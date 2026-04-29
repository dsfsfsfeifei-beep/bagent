from .mapping import get_field_mapping
from .supplier import get_supplier, search_suppliers
from .sync import get_sync_log, get_sync_status
from .ui import (
    confirm_with_user,
    highlight_element,
    navigate_to,
    open_supplier_detail,
    prefill_form,
)

DATA_TOOLS = [
    get_supplier,
    search_suppliers,
    get_sync_status,
    get_sync_log,
    get_field_mapping,
]

UI_TOOLS = [
    navigate_to,
    open_supplier_detail,
    highlight_element,
    prefill_form,
    confirm_with_user,
]

ALL_TOOLS = DATA_TOOLS + UI_TOOLS
