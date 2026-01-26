import os
import json
import streamlit as st
import streamlit.components.v1 as components
from typing import List, Dict, Any, Union, Optional

# Create a _RELEASE constant. We'll set this to False while we're developing
# the component, and True when we're ready to package and distribute it.
# (This is, of course, optional - there are innumerable ways to manage your
# release process.)
_RELEASE = True

# Declare a Streamlit component. `declare_component` returns a function
# that is used to create instances of the component. We're naming this
# function "_component_func", with an underscore prefix, because we don't want
# to expose it directly to users. Instead, we will create a custom wrapper
# function, below, that will serve as our component's public API.

# It's worth noting that this call to `declare_component` is the
# *only thing* you need to do to create the binding between Streamlit and
# your component frontend. Everything else we do in this file is simply a
# best practice.

if not _RELEASE:
    _component_func = components.declare_component(
        # We give the component a simple, descriptive name ("code_editor"
        # does not fit this bill, so please choose something better for your
        # own component :)
        "code_editor",
        # Pass `url` here to tell Streamlit that the component will be served
        # by the local dev server that you run via `npm run start`.
        # (This is useful while your component is in development.)
        url="http://localhost:3001",
    )
else:
    # When we're distributing a production version of the component, we'll
    # replace the `url` param with `path`, and point it to to the component's
    # build directory:
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(parent_dir, "assets")
    _component_func = components.declare_component(
        "code_editor", path=build_dir)


# Create a wrapper function for the component. This is an optional
# best practice - we could simply expose the component function returned by
# `declare_component` and call it done. The wrapper allows us to customize
# our component's API: we can pre-process its input args, post-process its
# output value, and add a docstring for users.
def code_editor(code: str, lang: str = 'python', theme: str = "default", shortcuts: str = "vscode", height: Union[int, List[int]] = 30, focus: bool = False, allow_reset: bool = False, replace_completer: bool = False, response_mode: str = "default", ghost_text: str = "", snippets: List[str] = ["", ""], completions: List[Any] = [], keybindings: Dict[str, Any] = {}, buttons: List[Any] = [], menu: Dict[str, Any] = {}, info: Dict[str, Any] = {}, options: Dict[str, Any] = {}, props: Dict[str, Any] = {}, editor_props: Dict[str, Any] = {}, component_props: Dict[str, Any] = {}, key: Optional[str] = None):
    """Create a new instance of "code_editor".

    Parameters
    ----------
    code: str
        The code that goes in the editor
    key: str or None
        An optional key that uniquely identifies this component. If this is
        None, and the component's arguments are changed, the component will
        be re-mounted in the Streamlit frontend and lose its current state.

    Returns
    -------
    dict
        Contains the type of event and the code inside the editor when 
        event occured
    """
    # Call through to our private component function. Arguments we pass here
    # will be sent to the frontend, where they'll be available in an "args"
    # dictionary.
    #
    # "default" is a special argument that specifies the initial return
    # value of the component before the user has interacted with it.
    component_value = _component_func(code=code, lang=lang, theme=theme, key=key, height=height, focus=focus, shortcuts=shortcuts, snippets=snippets, completions=completions, keybindings=keybindings, buttons=buttons, options=options, props=props, editor_props=editor_props,
                                      component_props=component_props, menu=menu, info=info, allow_reset=allow_reset, replace_completer=replace_completer, response_mode=response_mode, ghost_text=ghost_text, default={"id": "", "type": "", "lang": "", "text": "", "selected": "", "cursor": ""})

    # We could modify the value returned from the component if we wanted.
    # There's no need to do this in our simple example - but it's an option.
    return component_value
