import streamlit as st
import json
from datetime import datetime

def init_session_state():
    if 'datasets' not in st.session_state:
        st.session_state.datasets = {}
    if 'recipe_steps' not in st.session_state:
        st.session_state.recipe_steps = []
    if 'last_added_id' not in st.session_state:
        st.session_state.last_added_id = None
    if 'active_base_dataset' not in st.session_state:
        st.session_state.active_base_dataset = None
    # Inputs
    if 'file_path_buffer' not in st.session_state:
        st.session_state.file_path_buffer = ""

def move_step(index, direction):
    steps = st.session_state.recipe_steps
    if direction == -1 and index > 0:
        steps[index], steps[index-1] = steps[index-1], steps[index]
    elif direction == 1 and index < len(steps) - 1:
        steps[index], steps[index+1] = steps[index+1], steps[index]
    st.session_state.last_added_id = steps[index if direction == -
                                           1 else index+1]['id']


def delete_step(index):
    st.session_state.recipe_steps.pop(index)


def add_step(step_type, default_label):
    new_id = datetime.now().timestamp()
    st.session_state.recipe_steps.append(
        {"type": step_type, "label": default_label, "id": new_id, "params": {}})
    st.session_state.last_added_id = new_id


def load_recipe_from_json(uploaded_file):
    try:
        data = json.load(uploaded_file)
        st.session_state.recipe_steps = data
        st.success("Recipe loaded!")
    except Exception as e:
        st.error(f"Invalid JSON: {e}")
