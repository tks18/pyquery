import streamlit as st
import json
from datetime import datetime

def init_session_state():
    # 'datasets' Removed: Engine holds them now.
    
    # Stores recipes for each dataset: { "dataset_name": [steps...] }
    if 'all_recipes' not in st.session_state:
        st.session_state.all_recipes = {}
        
    # We still keep this for UI binding compatibility
    if 'recipe_steps' not in st.session_state:
        st.session_state.recipe_steps = []
        
    if 'last_added_id' not in st.session_state:
        st.session_state.last_added_id = None
    if 'active_base_dataset' not in st.session_state:
        st.session_state.active_base_dataset = None
    # Inputs
    if 'file_path_buffer' not in st.session_state:
        st.session_state.file_path_buffer = ""

def get_active_recipe():
    active_ds = st.session_state.active_base_dataset
    if active_ds and active_ds in st.session_state.all_recipes:
        return st.session_state.all_recipes[active_ds]
    return []

def move_step(index, direction):
    # Relies on session state for recipe management (Frontend concern)
    active_ds = st.session_state.active_base_dataset
    if not active_ds: return

    steps = st.session_state.all_recipes[active_ds]
    if direction == -1 and index > 0:
        steps[index], steps[index-1] = steps[index-1], steps[index]
    elif direction == 1 and index < len(steps) - 1:
        steps[index], steps[index+1] = steps[index+1], steps[index]
    st.session_state.last_added_id = steps[index if direction == -
                                           1 else index+1]['id']
    st.session_state.recipe_steps = steps

def delete_step(index):
    active_ds = st.session_state.active_base_dataset
    if active_ds:
        st.session_state.all_recipes[active_ds].pop(index)
        st.session_state.recipe_steps = st.session_state.all_recipes[active_ds]

def add_step(step_type, default_label):
    active_ds = st.session_state.active_base_dataset
    if not active_ds:
        st.error("No active dataset selected to add step to.")
        return

    new_id = datetime.now().timestamp()
    new_step = {"type": step_type, "label": default_label, "id": new_id, "params": {}}
    
    if active_ds not in st.session_state.all_recipes:
        st.session_state.all_recipes[active_ds] = []
        
    st.session_state.all_recipes[active_ds].append(new_step)
    st.session_state.last_added_id = new_id
    st.session_state.recipe_steps = st.session_state.all_recipes[active_ds]

def load_recipe_from_json(uploaded_file):
    active_ds = st.session_state.active_base_dataset
    if not active_ds:
        st.error("No active dataset to load recipe into.")
        return

    try:
        data = json.load(uploaded_file)
        st.session_state.all_recipes[active_ds] = data
        st.session_state.recipe_steps = data
        st.success("Recipe loaded!")
    except Exception as e:
        st.error(f"Invalid JSON: {e}")
