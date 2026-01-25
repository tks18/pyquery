from typing import List, Optional, Dict, Any, Union

import streamlit as st

from pyquery_polars.frontend.custom_components import code_editor
from pyquery_polars.frontend.utils.completions import get_standard_pyquery_completions, get_sql_completions


def _base_editor(
    code: str,
    language: str = "python",
    key: str = "editor",
    height: Union[int, List[int]] = [10, 20],
    read_only: bool = False,
    completions: Optional[List[Dict[str, Any]]] = None,
    info: Optional[Dict[str, Any]] = None,
    extra_buttons: Optional[List[Dict[str, Any]]] = None,
    options: Optional[Dict[str, Any]] = None
) -> Optional[str]:
    """
    Internal base editor component.
    """

    # Standard Attribution (Small footprint)
    st.markdown("""<small style="opacity: 0.7; display: block; margin-bottom: 5px;">
        Editor powered by <a href="https://github.com/bouzidanas/streamlit-code-editor" target="_blank" style="color: inherit;">streamlit-code-editor</a>.
    </small>""", unsafe_allow_html=True)

    # Standard Styling
    ace_props = {
        "style": {"borderRadius": "0px 0px 4px 4px"},
        "readOnly": read_only
    }

    # Base Buttons (can be overridden or extended)
    buttons = []
    if extra_buttons:
        buttons.extend(extra_buttons)

    # Default Ace Options if not provided
    if options is None:
        options = {
            "showLineNumbers": True,
            "showGutter": True,
            "highlightActiveLine": True,
            "wrap": True,
            "enableBasicAutocompletion": True,
            "enableLiveAutocompletion": True,
            "readOnly": read_only
        }

    response_dict = code_editor(
        code,
        lang=language,
        height=height,
        theme="monokai",
        key=key,
        props=ace_props,
        buttons=buttons,
        completions=completions or [],
        info=info or {},
        options=options
    )

    if response_dict and response_dict.get('type') == "submit" and len(response_dict['text']) != 0:
        # Event Deduplication: Check if we already processed this specific event ID
        event_id = response_dict.get('id')
        state_key = f"{key}_last_event_id"

        if event_id and st.session_state.get(state_key) != event_id:
            st.session_state[state_key] = event_id
            return response_dict['text']

    return None


def python_editor(
    code: str,
    key: str,
    height: Union[int, List[int]] = [10, 20],
    read_only: bool = False,
    completions: Optional[List[Dict[str, Any]]] = None,
    extra_buttons: Optional[List[Dict[str, Any]]] = None
) -> Optional[str]:
    """
    Highly customized Python editor.
    Includes standard 'Run' button if not in extra_buttons.
    """
    # Default to Run button if no buttons provided, or append to them
    final_buttons = [
        {
            "name": "Run",
            "feather": "Play",
            "primary": True,
            "hasText": True,
            "showWithIcon": True,
            "commands": ["submit"],
            "style": {"bottom": "0.44rem", "right": "0.4rem"}
        },
        {
            "name": "Copy",
            "feather": "Copy",
            "hasText": True,
            "alwaysOn": True,
            "commands": ["copyAll"],
            "style": {"top": "0.44rem", "right": "0.4rem"}
        }
    ]
    if extra_buttons:
        # Avoid duplicates if caller passes their own
        final_buttons.extend(extra_buttons)

    # Auto-load standard PyQuery completions if not specifically overridden
    # Note: If the caller explicitly passes [], it suppresses this. None enables default.
    final_completions = completions
    if final_completions is None:
        try:
            final_completions = get_standard_pyquery_completions()
        except:
            final_completions = []

    return _base_editor(
        code=code,
        language="python",
        key=key,
        height=height,
        read_only=read_only,
        completions=final_completions,
        extra_buttons=final_buttons
    )


def sql_editor(
    code: str,
    key: str,
    height: Union[int, List[int]] = [15, 20],  # Taller default for SQL
    read_only: bool = False,
    completions: Optional[List[Dict[str, Any]]] = None
) -> Optional[str]:
    """
    Highly customized SQL editor.
    """
    buttons = [
        {
            "name": "Run Query",
            "feather": "Play",
            "primary": True,
            "hasText": True,
            "showWithIcon": True,
            "commands": ["submit"],
            "style": {"bottom": "0.44rem", "right": "0.4rem"}
        },
        {
            "name": "Copy",
            "feather": "Copy",
            "hasText": True,
            "alwaysOn": True,
            "commands": ["copyAll"],
            "style": {"top": "0.44rem", "right": "0.4rem"}
        }
    ]

    # SQL specific keywords
    final_completions = completions
    if final_completions is None:
        try:
            final_completions = get_sql_completions()
        except:
            final_completions = []

    return _base_editor(
        code=code,
        language="sql",
        key=key,
        height=height,
        read_only=read_only,
        completions=final_completions,
        extra_buttons=buttons
    )
