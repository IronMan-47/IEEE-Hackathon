from typing import Set

LIVING_CANVAS_OPS: Set[str] = {
    "CREATE_ELEMENT",
    "UPDATE_ELEMENT",
    "DELETE_ELEMENT",
    "MOVE_ELEMENT",
    "RESIZE_ELEMENT",
    "UPDATE_STYLE",
    "UPDATE_TEXT",
    "GROUP_ELEMENTS",
    "UNGROUP_ELEMENTS",
    "RENAME_ELEMENT",
    "REORDER_ELEMENT",
    "UPDATE_PROPERTY",
    "ADD_ELEMENT",
    "REMOVE_ELEMENT"
}

VSCODE_OPS: Set[str] = {
    "CODE_CHANGE",
    "REFACTOR",
    "FORMAT_CODE"
}

BROWSER_OPS: Set[str] = {
    "NAVIGATE_SAFE",
    "CLICK_ELEMENT",
    "ENTER_NON_SENSITIVE_TEXT",
    "SELECT_OPTION",
    "SCROLL_TO_ELEMENT",
    "SUBMIT_FORM"
}

TERMINAL_OPS: Set[str] = {
    "TERMINAL_INSPECT"
}

FIGMA_OPS: Set[str] = {
    "FIGMA_INSPECT"
}

# The union of all valid, known system operations across domains
ALL_KNOWN_OPS: Set[str] = (
    LIVING_CANVAS_OPS |
    VSCODE_OPS |
    BROWSER_OPS |
    TERMINAL_OPS |
    FIGMA_OPS
)
