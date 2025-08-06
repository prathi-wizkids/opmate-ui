# milestones_manage.py
import streamlit as st
import requests
import pandas as pd

# --- Configuration ---
#API_BASE_URL = "http://localhost:5002" # Your Node.js API URL
from config import API_BASE_URL

# --- Level Mapping (MUST be consistent with API) ---
LEVEL_MAPPING = {
    "G1": ["L1", "L2", "L3", "L4"],
    "G2": ["L5", "L6", "L7", "L8"],
    "G3": ["L9", "L10", "L11", "L12"],
    "G4": ["L13", "L14", "L15", "L16"],
}
ALL_POSSIBLE_LEVELS = sorted(list(set(level for levels in LEVEL_MAPPING.values() for level in levels)))


# --- API Interaction Functions for Milestones ---

def get_all_milestones():
    """Fetches all milestones from the backend API."""
    try:
        response = requests.get(f"{API_BASE_URL}/milestones")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching milestones: {e}")
        return []

def create_milestone(milestone_class, level, oid):
    """Creates a new milestone."""
    try:
        response = requests.post(f"{API_BASE_URL}/milestones", json={"class": milestone_class, "level": level, "oid": oid})
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error creating milestone: {e}")
        return None

def update_milestone(mid, milestone_class=None, level=None, oid=None):
    """Updates an existing milestone."""
    payload = {}
    if milestone_class is not None:
        payload["class"] = milestone_class
    if level is not None:
        payload["level"] = level
    if oid is not None:
        payload["oid"] = oid
    
    try:
        response = requests.put(f"{API_BASE_URL}/milestones/{mid}", json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error updating milestone: {e}")
        return None

def delete_milestone(mid):
    """Deletes a milestone."""
    try:
        response = requests.delete(f"{API_BASE_URL}/milestones/{mid}")
        response.raise_for_status()
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        st.error(f"Error deleting milestone: {e}")
        return False

# --- API Interaction Functions for Gurukul Offerings (re-used) ---

def get_all_gurukul_offerings():
    """Fetches all gurukul offerings from the backend API."""
    try:
        response = requests.get(f"{API_BASE_URL}/gurukul-offerings")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching gurukul offerings: {e}")
        return []

def get_all_gurukuls_for_dropdown():
    """Fetches all gurukuls (gid, gname) for use in dropdowns (for display purposes)."""
    try:
        response = requests.get(f"{API_BASE_URL}/gurukul")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching gurukuls for dropdown: {e}")
        return []


# --- Streamlit UI for Milestone Management ---

def milestones_manage_page():
    """Renders the UI for managing Milestones."""
    st.header("Manage Milestones")
    st.write("Here you can create, view, update, and delete Milestones.")

    # Fetch all necessary data
    all_milestones = get_all_milestones()
    all_gurukul_offerings = get_all_gurukul_offerings()
    all_gurukuls = get_all_gurukuls_for_dropdown()

    # Create maps for easy lookup
    gurukul_id_to_name_map = {g['gid']: g['gname'] for g in all_gurukuls}
    offering_id_to_details_map = {o['oid']: o for o in all_gurukul_offerings}
    
    # Group existing milestones by offering (oid) and level to prevent duplicates
    # This assumes a milestone is unique by (oid, level)
    milestone_oid_level_map = {}
    for m in all_milestones:
        key = (m['oid'], m['level'])
        milestone_oid_level_map[key] = m['mid']


    # --- Create New Milestone Section ---
    st.subheader("Create New Milestone")
    if not all_gurukuls:
        st.info("No Gurukuls available. Please create Gurukuls first.")
        st.markdown("---")
        return # Exit function if no gurukuls

    # 1. Select Gurukul for Creation
    gurukul_display_options_create = [f"{g['gname']} (ID: {g['gid']})" for g in all_gurukuls]
    selected_gurukul_create_display = st.selectbox(
        "Select Gurukul for new Milestone",
        options=gurukul_display_options_create,
        key="create_milestone_gurukul_select"
    )
    selected_gurukul_create_id = int(selected_gurukul_create_display.split("(ID: ")[1][:-1]) if selected_gurukul_create_display else None

    # Filter offerings based on selected Gurukul
    filtered_offerings_for_create = [
        o for o in all_gurukul_offerings if o['gid'] == selected_gurukul_create_id
    ]
    offering_display_options_create = []
    if filtered_offerings_for_create:
        for o in filtered_offerings_for_create:
            offering_display_options_create.append(f"OID: {o['oid']} (Type: {o['gtype']})")
    else:
        st.info(f"No Gurukul Offerings found for '{selected_gurukul_create_display}'. Please create offerings for this Gurukul first.")
        st.markdown("---")
        return # Exit if no offerings for selected gurukul

    # 2. Select Offering for Creation (filtered by Gurukul)
    selected_offering_create_display = st.selectbox(
        "Select Parent Gurukul Offering (OID) for new Milestone",
        options=offering_display_options_create,
        key="create_milestone_offering_select"
    )
    
    selected_offering_create_oid = None
    selected_offering_gtype = None
    if selected_offering_create_display:
        selected_offering_create_oid = int(selected_offering_create_display.split("OID: ")[1].split(" ")[0])
        selected_offering_details = offering_id_to_details_map.get(selected_offering_create_oid)
        if selected_offering_details:
            selected_offering_gtype = selected_offering_details['gtype']

    # Dynamic filtering of Levels based on selected Gurukul Offering's gtype
    available_levels_for_creation_current_selection = []
    if selected_offering_gtype:
        all_levels_for_gtype = LEVEL_MAPPING.get(selected_offering_gtype, [])
        existing_levels_for_oid = {level for oid, level in milestone_oid_level_map if oid == selected_offering_create_oid}
        
        available_levels_for_creation_current_selection = [
            lvl for lvl in all_levels_for_gtype if lvl not in existing_levels_for_oid
        ]
        available_levels_for_creation_current_selection.sort()

    # --- Debugging Information (Create Section) ---
    print(f"DEBUG (Create): Selected Gurukul ID: {selected_gurukul_create_id}")
    print(f"DEBUG (Create): Selected Offering OID: {selected_offering_create_oid}")
    print(f"DEBUG (Create): Selected Offering GType: {selected_offering_gtype}")
    print(f"DEBUG (Create): Existing Levels for this OID: {list(existing_levels_for_oid) if selected_offering_create_oid else 'N/A'}")
    print(f"DEBUG (Create): Available Levels for dropdown: {available_levels_for_creation_current_selection}")
    # --- End Debugging Information ---

    with st.form("create_milestone_form"):
        milestone_class = st.number_input("Class", min_value=1, value=1, key="new_milestone_class")
        
        new_level = None
        if available_levels_for_creation_current_selection:
            new_level = st.selectbox(
                "Level", 
                options=available_levels_for_creation_current_selection, 
                key="new_milestone_level_select_in_form"
            )
        else:
            st.info(f"The selected Gurukul Offering (OID: {selected_offering_create_oid}) already has all possible levels ({selected_offering_gtype} levels) or no levels are defined for its GType.")
            new_level = None

        create_submitted = st.form_submit_button("Create Milestone")

        if create_submitted:
            if selected_offering_create_oid is not None and new_level:
                with st.spinner("Creating milestone..."):
                    result = create_milestone(milestone_class, new_level, selected_offering_create_oid)
                    if result:
                        st.success(f"Milestone (ID: {result['mid']}, Level: {result['level']}) created successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to create milestone. This might be a duplicate or refer to a non-existent Gurukul Offering. Please check API logs.")
            else:
                st.warning("Please select a Gurukul Offering and an available Level.")
    
    st.markdown("---") # Separator

    # --- List Existing Milestones Section ---
    st.subheader("Existing Milestones")
    if all_milestones:
        # Enhance with Gurukul and Offering names for better display
        displayed_milestones = []
        for m in all_milestones:
            offering_details = offering_id_to_details_map.get(m['oid'])
            gurukul_name = "N/A"
            offering_type = "N/A"
            if offering_details:
                gurukul_name = gurukul_id_to_name_map.get(offering_details['gid'], "N/A")
                offering_type = offering_details['gtype']
            
            displayed_milestones.append({
                "mid": m['mid'],
                "class": m['class'],
                "level": m['level'],
                "oid": m['oid'],
                "offering_type": offering_type,
                "gurukul_name": gurukul_name
            })
        
        df_milestones = pd.DataFrame(displayed_milestones)
        df_milestones = df_milestones[['mid', 'class', 'level', 'offering_type', 'gurukul_name', 'oid']]
        st.dataframe(df_milestones, use_container_width=True)
    else:
        st.info("No milestones found yet.")

    st.markdown("---") # Separator

    # --- Update Existing Milestone Section ---
    st.subheader("Update Existing Milestone")
    if not all_milestones:
        st.info("No milestones available to update.")
        st.markdown("---")
        return # Exit if no milestones

    if not all_gurukuls:
        st.info("No Gurukuls available for selection in update. Please create Gurukuls.")
        st.markdown("---")
        return # Exit if no gurukuls

    # 1. Select Gurukul for Update
    gurukul_display_options_update = [f"{g['gname']} (ID: {g['gid']})" for g in all_gurukuls]
    selected_gurukul_update_display = st.selectbox(
        "Select Gurukul for Milestone Update",
        options=gurukul_display_options_update,
        key="update_milestone_gurukul_select"
    )
    selected_gurukul_update_id = int(selected_gurukul_update_display.split("(ID: ")[1][:-1]) if selected_gurukul_update_display else None

    # Filter offerings based on selected Gurukul
    filtered_offerings_for_update = [
        o for o in all_gurukul_offerings if o['gid'] == selected_gurukul_update_id
    ]
    offering_display_options_update = []
    if filtered_offerings_for_update:
        for o in filtered_offerings_for_update:
            offering_display_options_update.append(f"OID: {o['oid']} (Type: {o['gtype']})")
    else:
        st.info(f"No Gurukul Offerings found for '{selected_gurukul_update_display}'. Cannot update milestones belonging to this Gurukul.")
        st.markdown("---")
        return # Exit if no offerings for selected gurukul

    # 2. Select Offering for Update (filtered by Gurukul)
    selected_offering_update_display = st.selectbox(
        "Select Parent Gurukul Offering (OID) for Milestone Update",
        options=offering_display_options_update,
        key="update_milestone_offering_select"
    )
    selected_offering_update_oid = int(selected_offering_update_display.split("OID: ")[1].split(" ")[0]) if selected_offering_update_display else None

    # Filter milestones based on selected Offering
    milestones_for_selected_offering = [
        m for m in all_milestones if m['oid'] == selected_offering_update_oid
    ]
    if not milestones_for_selected_offering:
        st.info(f"No milestones found for the selected Gurukul Offering (OID: {selected_offering_update_oid}).")
        st.markdown("---")
        return # Exit if no milestones for selected offering

    # 3. Select Milestone to Update (filtered by Offering)
    sorted_milestones_for_update = sorted(milestones_for_selected_offering, key=lambda x: x['mid'])
    milestone_options_update = {
        f"ID: {m['mid']} (Level: {m['level']})": m['mid'] 
        for m in sorted_milestones_for_update
    }
    selected_milestone_display = st.selectbox(
        "Select Specific Milestone to Update",
        options=list(milestone_options_update.keys()),
        key="select_specific_milestone_to_update"
    )
    selected_milestone_id = milestone_options_update.get(selected_milestone_display)

    # Initialize variables with default/safe values
    initial_class = 1 
    initial_oid = selected_offering_update_oid # Default to the currently selected offering's OID
    initial_level = None
    
    current_milestone_obj = None
    if selected_milestone_id is not None:
        current_milestone_obj = next((m for m in all_milestones if m['mid'] == selected_milestone_id), None)

    if current_milestone_obj:
        initial_class = current_milestone_obj['class']
        initial_oid = current_milestone_obj['oid']
        initial_level = current_milestone_obj['level']

    updated_offering_details_gtype = offering_id_to_details_map.get(initial_oid, {}).get('gtype')

    # Calculate available levels based on the *current/selected* OID's gtype
    available_levels_for_update = []
    if updated_offering_details_gtype:
        all_levels_for_updated_gtype = LEVEL_MAPPING.get(updated_offering_details_gtype, [])
        
        existing_levels_for_selected_oid_excluding_current = set()
        for oid_key, level_key in milestone_oid_level_map:
            if oid_key == initial_oid: # Check against the initial_oid which is the current milestone's oid
                if not (oid_key == initial_oid and level_key == initial_level and milestone_oid_level_map.get((oid_key, level_key)) == selected_milestone_id):
                    existing_levels_for_selected_oid_excluding_current.add(level_key)
        
        available_levels_for_update = [
            lvl for lvl in all_levels_for_updated_gtype if lvl not in existing_levels_for_selected_oid_excluding_current
        ]
    available_levels_for_update.sort()

    # --- Debugging Information (Update Section) ---
    print(f"DEBUG (Update): Selected Milestone ID: {selected_milestone_id}")
    print(f"DEBUG (Update): Current OID: {initial_oid}, Current Level: {initial_level}, Current Class: {initial_class}")
    print(f"DEBUG (Update): GType of current Offering ({initial_oid}): {updated_offering_details_gtype}")
    print(f"DEBUG (Update): Levels defined for GType: {LEVEL_MAPPING.get(updated_offering_details_gtype, [])}")
    print(f"DEBUG (Update): Existing Levels for current OID (excluding current milestone's): {list(existing_levels_for_selected_oid_excluding_current)}")
    print(f"DEBUG (Update): Available Levels for new Level dropdown: {available_levels_for_update}")
    # --- End Debugging Information ---


    with st.form("update_milestone_form"):
        updated_class = st.number_input("New Class", min_value=1, value=max(1, initial_class), key="updated_milestone_class")
        
        # Set default index for updated_level based on whether initial_level is in available options
        initial_level_index_update_form = 0
        if initial_level in available_levels_for_update:
            initial_level_index_update_form = available_levels_for_update.index(initial_level)
        elif available_levels_for_update:
            pass 
        else:
            initial_level_index_update_form = -1 
        
        updated_level = None
        if available_levels_for_update:
            updated_level = st.selectbox(
                "New Level",
                options=available_levels_for_update,
                index=initial_level_index_update_form,
                key="updated_milestone_level_new_select_in_form"
            )
        else:
            st.warning(f"No valid levels available for the selected offering (OID: {initial_oid}) and its GType.")
            updated_level = None
        
        update_submitted = st.form_submit_button("Update Milestone")

        if update_submitted:
            if selected_milestone_id is not None and initial_oid is not None and updated_level: # initial_oid is the actual OID of selected milestone
                with st.spinner(f"Updating milestone ID {selected_milestone_id}..."):
                    update_payload = {}
                    if updated_class != initial_class:
                        update_payload['class'] = updated_class
                    
                    # For update, OID is fixed to the selected milestone's OID, only level can change within that OID's allowed levels
                    if updated_level != initial_level: 
                        update_payload['level'] = updated_level
                        # The OID does not change if we are updating an existing milestone's level within the same offering
                        # However, the API expects OID when level is passed.
                        update_payload['oid'] = initial_oid # Ensure OID is passed with level update
                    
                    if not update_payload:
                        st.info("No changes detected. Milestone not updated.")
                        st.rerun()
                        return

                    result = update_milestone(selected_milestone_id, **update_payload)
                    if result:
                        st.success(f"Milestone ID {result['mid']} updated successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to update milestone. This might be a duplicate, an invalid level for the new offering type, or refer to a non-existent Gurukul Offering. Please check API logs.")
            else:
                st.warning("Please select a milestone and provide valid details for update.")
        else:
            st.info("Select a milestone from the dropdown to see its details for update.")

    st.markdown("---") # Separator

    # --- Delete Milestone Section ---
    st.subheader("Delete Milestone")
    if all_milestones:
        milestone_options_delete = {f"ID: {m['mid']} (Level: {m['level']})": m['mid'] for m in sorted(all_milestones, key=lambda x: x['mid'])}
        selected_milestone_display_delete = st.selectbox(
            "Select Milestone to Delete",
            options=list(milestone_options_delete.keys()),
            key="delete_milestone_select"
        )
        selected_milestone_id_delete = milestone_options_delete.get(selected_milestone_display_delete)

        if st.button("Delete Milestone", key="delete_milestone_button"):
            if selected_milestone_id_delete is not None:
                st.session_state.confirm_delete_milestone_id = selected_milestone_id_delete
                st.warning(f"Are you sure you want to delete Milestone ID: {selected_milestone_id_delete}? This action cannot be undone.")
            else:
                st.warning("Please select a milestone to delete.")
        
        if 'confirm_delete_milestone_id' in st.session_state and st.session_state.confirm_delete_milestone_id == selected_milestone_id_delete:
            if st.button("Confirm Deletion", key="confirm_delete_milestone_final_button"):
                with st.spinner(f"Deleting milestone ID {selected_milestone_id_delete}..."):
                    success = delete_milestone(selected_milestone_id_delete)
                    if success:
                        st.success(f"Milestone ID {selected_milestone_id_delete} deleted successfully!")
                        del st.session_state.confirm_delete_milestone_id
                        st.rerun()
                    else:
                        st.error("Failed to delete milestone. Please check API logs.")
    else:
        st.info("No milestones available to delete.")
