# offerings_manage.py
import streamlit as st
import requests
import pandas as pd

# --- Configuration ---
API_BASE_URL = "http://localhost:5002" # Corrected API Base URL
ALL_GTYPES = ["G1", "G2", "G3", "G4"] # All possible offering types

# --- Level Mapping (MUST be consistent with API) ---
LEVEL_MAPPING = {
    "G1": ["L1", "L2", "L3", "L4"],
    "G2": ["L5", "L6", "L7", "L8"],
    "G3": ["L9", "L10", "L11", "L12"],
    "G4": ["L13", "L14", "L15", "L16"],
}
# Note: ALL_POSSIBLE_LEVELS is not directly used in offerings_manage.py
ALL_POSSIBLE_LEVELS = sorted(list(set(level for levels in LEVEL_MAPPING.values() for level in levels)))

# --- API Interaction Functions ---

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
    """Fetches all gurukuls (gid, gname) for use in dropdowns."""
    try:
        response = requests.get(f"{API_BASE_URL}/gurukul")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching gurukuls for dropdown: {e}")
        return []

def create_gurukul_offering(gid, gtype):
    """Creates a new gurukul offering."""
    try:
        response = requests.post(f"{API_BASE_URL}/gurukul-offerings", json={"gid": gid, "gtype": gtype})
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error creating gurukul offering: {e}")
        return None

def update_gurukul_offering(oid, gid, gtype):
    """Updates an existing gurukul offering."""
    try:
        response = requests.put(f"{API_BASE_URL}/gurukul-offerings/{oid}", json={"gid": gid, "gtype": gtype})
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error updating gurukul offering: {e}")
        return None

def delete_gurukul_offering(oid):
    """Deletes a gurukul offering."""
    try:
        response = requests.delete(f"{API_BASE_URL}/gurukul-offerings/{oid}")
        response.raise_for_status()
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        st.error(f"Error deleting gurukul offering: {e}")
        return False

# --- Streamlit UI for Gurukul Offering Management ---

def offerings_manage_page():
    """Renders the UI for managing Gurukul Offerings."""
    st.header("Manage Gurukul Offerings")
    st.write("Here you can create, view, update, and delete Gurukul Offerings.")

    # Fetch all gurukuls and offerings
    gurukuls = get_all_gurukuls_for_dropdown()
    all_offerings = get_all_gurukul_offerings()

    # Create a map for gurukul names (ID to Name)
    gurukul_id_to_name_map = {g['gid']: g['gname'] for g in gurukuls}

    # Group existing offerings by gurukul ID to check for completeness
    gurukul_offerings_map = {}
    for offering in all_offerings:
        gid = offering['gid']
        gtype = offering['gtype']
        if gid not in gurukul_offerings_map:
            gurukul_offerings_map[gid] = set()
        gurukul_offerings_map[gid].add(gtype)

    # Filter gurukuls that DO NOT have all G-types
    creatable_gurukuls = []
    for g in gurukuls:
        gid = g['gid']
        existing_gtypes = gurukul_offerings_map.get(gid, set())
        if not all(gt in existing_gtypes for gt in ALL_GTYPES):
            creatable_gurukuls.append(g)
    
    # Sort creatable gurukuls by name for consistent display
    creatable_gurukuls.sort(key=lambda x: x['gname'])

    # Create display options for creatable gurukuls
    creatable_gurukul_display_options = [f"{g['gname']} (ID: {g['gid']})" for g in creatable_gurukuls]

    # --- Create Gurukul Offering Section ---
    st.subheader("Create New Gurukul Offering")
    if creatable_gurukuls:
        # Moved outside the form to allow immediate re-rendering of GType dropdown
        selected_gurukul_create_display = st.selectbox(
            "Select Parent Gurukul",
            options=creatable_gurukul_display_options,
            key="create_offering_gurukul_select"
        )
        
        # Extract GID from the display string
        selected_gurukul_create_id = None
        if selected_gurukul_create_display:
            selected_gurukul_create_id = int(selected_gurukul_create_display.split("(ID: ")[1][:-1])

        # Dynamic filtering of GTypes based on selected Gurukul
        available_gtypes_for_creation_current_selection = []
        if selected_gurukul_create_id is not None:
            existing_gtypes_for_selected_gurukul = gurukul_offerings_map.get(selected_gurukul_create_id, set())
            available_gtypes_for_creation_current_selection = [
                gt for gt in ALL_GTYPES if gt not in existing_gtypes_for_selected_gurukul
            ]
            available_gtypes_for_creation_current_selection.sort()

        # --- Debugging Information ---
        print(f"DEBUG (Create): Selected Gurukul ID: {selected_gurukul_create_id}")
        print(f"DEBUG (Create): Existing GTypes for selected Gurukul: {list(existing_gtypes_for_selected_gurukul)}")
        print(f"DEBUG (Create): Available GTypes for dropdown: {available_gtypes_for_creation_current_selection}")
        # --- End Debugging Information ---

        with st.form("create_offering_form"):
            new_gtype = None
            if available_gtypes_for_creation_current_selection:
                new_gtype = st.selectbox(
                    "Offering Type", 
                    options=available_gtypes_for_creation_current_selection, 
                    key="new_offering_gtype_select_in_form" # Added _in_form to key for uniqueness
                )
            else:
                st.info(f"The selected Gurukul '{selected_gurukul_create_display}' already has all possible offering types (G1-G4).")
                new_gtype = None # Ensure it's explicitly None if no options

            create_submitted = st.form_submit_button("Create Offering")

            if create_submitted:
                if selected_gurukul_create_id is not None and new_gtype:
                    with st.spinner("Creating offering..."):
                        result = create_gurukul_offering(selected_gurukul_create_id, new_gtype)
                        if result:
                            st.success(f"Offering '{result['gtype']}' (ID: {result['oid']}) created for Gurukul ID {result['gid']} successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to create offering. This might be a duplicate for the selected Gurukul or an invalid GType. Please check API logs.")
                else:
                    st.warning("Please select a parent Gurukul and an Offering Type.")
    else:
        st.info("All Gurukuls already have all possible offering types (G1-G4) assigned. Cannot create new offerings unless a Gurukul offering is deleted.")


    st.markdown("---")

    # --- List Gurukul Offerings Section ---
    st.subheader("Existing Gurukul Offerings")
    
    if all_offerings:
        # Enhance offerings with Gurukul names for better readability
        for offering in all_offerings:
            offering['gurukul_name'] = gurukul_id_to_name_map.get(offering['gid'], "N/A")
        
        df_offerings = pd.DataFrame(all_offerings)
        # Reorder columns for display
        df_offerings = df_offerings[['oid', 'gurukul_name', 'gid', 'gtype']]
        st.dataframe(df_offerings, use_container_width=True)
    else:
        st.info("No gurukul offerings found yet.")

    st.markdown("---")

    # --- Update Gurukul Offering Section ---
    st.subheader("Update Existing Gurukul Offering")
    if all_offerings:
        # Sort offerings for consistent display in selectbox
        sorted_offerings = sorted(all_offerings, key=lambda x: x['oid'])

        offering_options = {
            f"ID: {o['oid']} ({o['gtype']} for {gurukul_id_to_name_map.get(o['gid'], 'N/A')})": o['oid'] 
            for o in sorted_offerings
        }
        selected_offering_display = st.selectbox(
            "Select Offering to Update",
            options=list(offering_options.keys()),
            key="update_offering_select"
        )

        selected_offering_id = offering_options.get(selected_offering_display)
        
        current_offering_obj = None
        if selected_offering_id is not None:
            current_offering_obj = next((o for o in all_offerings if o['oid'] == selected_offering_id), None)

        with st.form("update_offering_form"):
            initial_gurukul_id = current_offering_obj['gid'] if current_offering_obj else (gurukuls[0]['gid'] if gurukuls else None)
            initial_gtype = current_offering_obj['gtype'] if current_offering_obj else ALL_GTYPES[0]

            # Pre-select the current Gurukul for update
            initial_gurukul_display = f"{gurukul_id_to_name_map.get(initial_gurukul_id, 'N/A')} (ID: {initial_gurukul_id})" if initial_gurukul_id else (all_gurukul_display_options[0] if all_gurukul_display_options else "")

            # Ensure all gurukuls are available for selection when updating
            all_gurukul_display_options = [f"{g['gname']} (ID: {g['gid']})" for g in gurukuls]
            
            updated_gurukul_display = st.selectbox(
                "New Parent Gurukul",
                options=all_gurukul_display_options,
                index=all_gurukul_display_options.index(initial_gurukul_display) if initial_gurukul_display in all_gurukul_display_options else 0,
                key="update_offering_gurukul_new_select"
            )
            updated_gurukul_id = int(updated_gurukul_display.split("(ID: ")[1][:-1]) if updated_gurukul_display else None

            # All G_TYPES are available for selection during update; backend handles uniqueness
            updated_gtype = st.selectbox(
                "New Offering Type",
                options=ALL_GTYPES,
                index=ALL_GTYPES.index(initial_gtype) if initial_gtype in ALL_GTYPES else 0,
                key="update_offering_gtype_new_select"
            )
            
            update_submitted = st.form_submit_button("Update Offering")

            if update_submitted:
                if selected_offering_id is not None and updated_gurukul_id is not None and updated_gtype:
                    with st.spinner(f"Updating offering ID {selected_offering_id}..."):
                        result = update_gurukul_offering(selected_offering_id, updated_gurukul_id, updated_gtype)
                        if result:
                            st.success(f"Offering ID {result['oid']} updated successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to update offering. This might be a duplicate for the selected Gurukul or refer to a non-existent Gurukul. Please check API logs.")
                else:
                    st.warning("Please select an offering and provide valid details.")
    else:
        st.info("No gurukul offerings available to update.")

    st.markdown("---")

    # --- Delete Gurukul Offering Section ---
    st.subheader("Delete Gurukul Offering")
    if all_offerings:
        # Sort offerings for consistent display in selectbox
        sorted_offerings_delete = sorted(all_offerings, key=lambda x: x['oid'])

        offering_options_delete = {
            f"ID: {o['oid']} ({o['gtype']} for {gurukul_id_to_name_map.get(o['gid'], 'N/A')})": o['oid'] 
            for o in sorted_offerings_delete
        }
        selected_offering_display_delete = st.selectbox(
            "Select Offering to Delete",
            options=list(offering_options_delete.keys()),
            key="delete_offering_select"
        )
        selected_offering_id_delete = offering_options_delete.get(selected_offering_display_delete)

        if st.button("Delete Offering", key="delete_offering_button"):
            if selected_offering_id_delete is not None:
                # Using a session state variable for confirmation
                st.session_state.confirm_delete_offering_id = selected_offering_id_delete
                st.warning(f"Are you sure you want to delete Gurukul Offering ID: {selected_offering_id_delete}? This action cannot be undone.")
            else:
                st.warning("Please select an offering to delete.")
        
        if 'confirm_delete_offering_id' in st.session_state and st.session_state.confirm_delete_offering_id == selected_offering_id_delete:
            if st.button("Confirm Deletion", key="confirm_delete_offering_final_button"):
                with st.spinner(f"Deleting offering ID {selected_offering_id_delete}..."):
                    success = delete_gurukul_offering(selected_offering_id_delete)
                    if success:
                        st.success(f"Gurukul Offering ID {selected_offering_id_delete} deleted successfully!")
                        del st.session_state.confirm_delete_offering_id
                        st.rerun()
                    else:
                        st.error("Failed to delete offering. Please check API logs.")
    else:
        st.info("No gurukul offerings available to delete.")

