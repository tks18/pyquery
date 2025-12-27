import streamlit as st
import json
import copy
from datetime import datetime
from typing import List
from pyquery_polars.core.models import RecipeStep
from pyquery_polars.core.registry import StepRegistry


def init_session_state():
    if 'all_recipes' not in st.session_state:
        st.session_state.all_recipes = {}

    if 'recipe_steps' not in st.session_state:
        st.session_state.recipe_steps = []

    if 'history_stack' not in st.session_state:
        st.session_state.history_stack = []
    if 'redo_stack' not in st.session_state:
        st.session_state.redo_stack = []

    if 'last_added_id' not in st.session_state:
        st.session_state.last_added_id = None
    if 'active_base_dataset' not in st.session_state:
        st.session_state.active_base_dataset = None
    if 'file_path_buffer' not in st.session_state:
        st.session_state.file_path_buffer = ""


def get_active_recipe() -> List[RecipeStep]:
    active_ds = st.session_state.active_base_dataset
    if active_ds and active_ds in st.session_state.all_recipes:
        return st.session_state.all_recipes[active_ds]
    return []


def save_checkpoint():
    """snapshots CURRENT state before a change"""
    active_ds = st.session_state.active_base_dataset
    if not active_ds:
        return
    
    current_steps = st.session_state.all_recipes.get(active_ds, [])
    # Deep copy needed because mutation happens in place
    snapshot = copy.deepcopy(current_steps)
    
    # Cap history stack to 20?
    if len(st.session_state.history_stack) > 20:
        st.session_state.history_stack.pop(0)

    st.session_state.history_stack.append(snapshot)
    # Clear redo stack on new branch
    st.session_state.redo_stack = []


def cleanup_widget_state(steps: List[RecipeStep]):
    """Clears Streamlit widget state for given steps to force UI refresh from params."""
    # Collect IDs
    step_ids = {s.id for s in steps}
    
    # Identify keys to remove
    keys_to_remove = []
    for key in st.session_state.keys():
        key_str = str(key)
        # Check if key contains any step ID
        # More robust than endswith, catches 'prefix_{id}_suffix'
        for sid in step_ids:
            if sid in key_str:
                keys_to_remove.append(key)
                break
                
    # Remove
    for k in keys_to_remove:
        del st.session_state[k]
        
    st.toast(f"Undo/Redo: Cleared {len(keys_to_remove)} widget states.")


def undo():
    active_ds = st.session_state.active_base_dataset
    if not active_ds or not st.session_state.history_stack:
        return
    
    # 1. Push current to Redo
    current = st.session_state.all_recipes.get(active_ds, [])
    st.session_state.redo_stack.append(copy.deepcopy(current))
    
    # 2. Pop from History
    prev_state = st.session_state.history_stack.pop()
    
    # 3. Regenerate IDs to force Widget Reset (Nuclear option for syncing)
    # This prevents stale widget state by ensuring all keys are fresh
    ts = int(datetime.now().timestamp() * 10000)
    for i, step in enumerate(prev_state):
        step.id = f"{ts}_{i}"
    
    # 4. Apply
    st.session_state.all_recipes[active_ds] = prev_state
    st.session_state.recipe_steps = prev_state
    
    # Cleanup call removed as ID regeneration handles it
    # cleanup_widget_state(prev_state + current)


def redo():
    active_ds = st.session_state.active_base_dataset
    if not active_ds or not st.session_state.redo_stack:
        return

    # 1. Push current to History
    current = st.session_state.all_recipes.get(active_ds, [])
    st.session_state.history_stack.append(copy.deepcopy(current))

    # 2. Pop from Redo
    next_state = st.session_state.redo_stack.pop()

    # 3. Regenerate IDs
    ts = int(datetime.now().timestamp() * 10000)
    for i, step in enumerate(next_state):
        step.id = f"{ts}_{i}"

    # 4. Apply
    st.session_state.all_recipes[active_ds] = next_state
    st.session_state.recipe_steps = next_state
    
    # Cleanup call removed
    # cleanup_widget_state(next_state + current)


def move_step(index, direction):
    save_checkpoint()
    active_ds = st.session_state.active_base_dataset
    if not active_ds:
        return

    steps = st.session_state.all_recipes[active_ds]
    if direction == -1 and index > 0:
        steps[index], steps[index-1] = steps[index-1], steps[index]
    elif direction == 1 and index < len(steps) - 1:
        steps[index], steps[index+1] = steps[index+1], steps[index]
    st.session_state.last_added_id = steps[index if direction == -
                                           1 else index+1].id
    st.session_state.recipe_steps = steps


def delete_step(index):
    save_checkpoint()
    active_ds = st.session_state.active_base_dataset
    if active_ds:
        st.session_state.all_recipes[active_ds].pop(index)
        st.session_state.recipe_steps = st.session_state.all_recipes[active_ds]


def add_step(step_type: str, default_label: str):
    active_ds = st.session_state.active_base_dataset
    if not active_ds:
        st.error("No active dataset selected to add step to.")
        return

    # Use Registry to get Default Params
    definition = StepRegistry.get(step_type)
    if not definition:
        st.error(f"Unknown step type: {step_type}")
        return

    # Instantiate the Params Model to get default values
    try:
        if definition.params_model:
            # Use TypeAdapter or just instantiation if it's a BaseModel class
            default_params_obj = definition.params_model()
            # Convert to dict for generic storage
            default_params_dict = default_params_obj.model_dump()
        else:
            default_params_dict = {}

    except Exception as e:
        st.error(f"Failed to init params: {e}")
        return

    save_checkpoint()

    new_id = str(datetime.now().timestamp())

    # Create Generic RecipeStep
    new_step = RecipeStep(
        id=new_id,
        type=step_type,
        label=default_label,
        params=default_params_dict
    )

    if active_ds not in st.session_state.all_recipes:
        st.session_state.all_recipes[active_ds] = []

    st.session_state.all_recipes[active_ds].append(new_step)
    st.session_state.last_added_id = new_id
    st.session_state.recipe_steps = st.session_state.all_recipes[active_ds]
    # Flag to suppress checkpoint on immediate sync
    st.session_state.just_added_step = True


def update_step_params(step_id: str, new_params: dict, create_checkpoint: bool = True):
    active_ds = st.session_state.active_base_dataset
    if not active_ds:
        return
        
    if create_checkpoint:
        save_checkpoint()

    steps = st.session_state.all_recipes.get(active_ds, [])
    for i, step in enumerate(steps):
        if step.id == step_id:
            step.params = new_params
            st.session_state.recipe_steps = steps
            st.session_state.all_recipes[active_ds] = steps  # Force write
            return


def load_recipe_from_json(uploaded_file):
    active_ds = st.session_state.active_base_dataset
    if not active_ds:
        st.error("No active dataset to load recipe into.")
        return

    try:
        data = json.load(uploaded_file)
        steps = []
        for s in data:
            steps.append(RecipeStep(**s))
        
        save_checkpoint()

        st.session_state.all_recipes[active_ds] = steps
        st.session_state.recipe_steps = steps
        st.success("Recipe loaded!")
    except Exception as e:
        st.error(f"Invalid JSON or Schema Mismatch: {e}")
