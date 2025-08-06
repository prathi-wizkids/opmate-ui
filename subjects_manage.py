# subjects_manage.py
import streamlit as st
import requests
import pandas as pd

# --- Configuration ---
API_BASE_URL = "http://localhost:5002" # Your Node.js API URL

# --- Level Mapping (MUST be consistent with API) ---
# This is used as a reference for all possible levels, but actual available levels
# are fetched from the milestones API.
LEVEL_MAPPING = {
    "G1": ["L1", "L2", "L3", "L4"],
    "G2": ["L5", "L6", "L7", "L8"],
    "G3": ["L9", "L10", "L11", "L12"],
    "G4": ["L13", "L14", "L15", "L16"],
}
ALL_POSSIBLE_LEVELS = sorted(list(set(level for levels in LEVEL_MAPPING.values() for level in levels)))

# --- API Interaction Functions for Subjects ---

def get_all_subjects():
    """Fetches all subjects from the backend API."""
    try:
        response = requests.get(f"{API_BASE_URL}/subjects")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching subjects: {e}")
        return []

def create_subject(subname, level, image_url):
    """Creates a new subject."""
    try:
        payload = {"subname": subname, "level": level}
        if image_url: # Only add image_url if it's not empty
            payload["image_url"] = image_url
        response = requests.post(f"{API_BASE_URL}/subjects", json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error creating subject: {e}")
        return None

def update_subject(subid, subname=None, level=None, image_url=None):
    """Updates an existing subject."""
    payload = {}
    if subname is not None:
        payload["subname"] = subname
    if level is not None:
        payload["level"] = level
    if image_url is not None: # Allow updating to empty string
        payload["image_url"] = image_url
    
    try:
        response = requests.put(f"{API_BASE_URL}/subjects/{subid}", json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error updating subject: {e}")
        return None

def delete_subject(subid):
    """Deletes a subject."""
    try:
        response = requests.delete(f"{API_BASE_URL}/subjects/{subid}")
        response.raise_for_status()
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        st.error(f"Error deleting subject: {e}")
        return False

# --- API Interaction Function for Milestones (to get distinct levels) ---

def get_distinct_milestone_levels():
    """Fetches all distinct levels present in the milestones table from the backend API."""
    try:
        response = requests.get(f"{API_BASE_URL}/milestones/distinct-levels")
        response.raise_for_status() # This will raise an exception for 4xx/5xx responses

        levels_data = response.json()
        
        # --- Debugging Information for API Response ---
        print(f"DEBUG: Raw API response JSON for distinct levels: {levels_data}")
        print(f"DEBUG: Type of levels_data: {type(levels_data)}")
        # --- End Debugging Information ---

        if not isinstance(levels_data, list):
            st.error(f"API response for distinct levels was not a list. Type: {type(levels_data)}, Content: {levels_data}")
            return []

        # List to hold the extracted levels
        extracted_levels = []
        for i, item in enumerate(levels_data):
            # --- Debugging Information for List Items ---
            print(f"DEBUG: Processing item {i}: {item}, Type: {type(item)}")
            # --- End Debugging Information ---
            if isinstance(item, str): # Corrected: Expect string directly
                extracted_levels.append(item)
            else:
                st.error(f"API response item {i} for distinct levels was not a string as expected. Item: {item}")
                # For robustness, we will continue and just skip this malformed item.
                
        if not extracted_levels:
            st.warning("No valid 'level' data (as strings) found in the distinct milestones API response. Check your database or API endpoint.")
            
        return sorted(extracted_levels)

    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching distinct milestone levels (RequestException): {e}")
        return []
    except ValueError: # Catch JSON decoding errors if response.json() fails
        st.error(f"API response for distinct levels was not valid JSON. Response text: {response.text}")
        return []
    except Exception as e:
        st.error(f"An unexpected error occurred while fetching distinct milestone levels: {e}")
        return []

# --- Streamlit UI for Subject Management ---

def subjects_manage_page():
    """Renders the UI for managing Subjects."""
    st.header("Manage Subjects")
    st.write("Here you can create, view, update, and delete Subjects.")

    # Fetch all necessary data
    all_subjects = get_all_subjects()
    # Fetch distinct levels that actually exist in the milestones table
    existing_milestone_levels = get_distinct_milestone_levels()

    # Filter ALL_POSSIBLE_LEVELS to only include those present in existing_milestone_levels
    available_levels_for_subjects = sorted([
        lvl for lvl in ALL_POSSIBLE_LEVELS if lvl in existing_milestone_levels
    ])

    if not available_levels_for_subjects:
        st.warning("No levels (L1-L16) found in the Milestones table. Cannot create/update subjects until milestones are added with defined levels.")

    # --- Create New Subject Section ---
    st.subheader("Create New Subject")
    with st.form("create_subject_form"):
        new_subname = st.text_input("Subject Name", key="new_subject_name_input")
        new_image_url = st.text_input("Image URL (optional)", key="new_subject_image_url_input")

        # Level selection for creation
        new_level = None
        if available_levels_for_subjects:
            new_level = st.selectbox(
                "Level",
                options=available_levels_for_subjects,
                key="new_subject_level_select"
            )
        else:
            st.info("No valid levels available from milestones to create a subject.")

        create_submitted = st.form_submit_button("Create Subject")

        if create_submitted:
            if new_subname and new_level:
                with st.spinner("Creating subject..."):
                    result = create_subject(new_subname, new_level, new_image_url)
                    if result:
                        st.success(f"Subject '{result['subname']}' (ID: {result['subid']}) created successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to create subject. Please check API logs. Ensure 'level' is valid and unique if applicable.")
            else:
                st.warning("Please enter Subject Name and select a valid Level.")
    
    st.markdown("---") # Separator

    # --- List Existing Subjects Section ---
    st.subheader("Existing Subjects")
    if all_subjects:
        df_subjects = pd.DataFrame(all_subjects)
        # Filter out 'isdeleted' column for display if it's always false for active subjects
        if 'isdeleted' in df_subjects.columns:
            df_subjects = df_subjects.drop(columns=['isdeleted'])
        st.dataframe(df_subjects, use_container_width=True)
    else:
        st.info("No subjects found yet.")

    st.markdown("---") # Separator

    # --- Update Existing Subject Section ---
    st.subheader("Update Existing Subject")
    if all_subjects:
        sorted_subjects = sorted(all_subjects, key=lambda x: x['subid'])
        subject_options = {
            f"ID: {s['subid']} ({s['subname']} - {s['level']})": s['subid'] 
            for s in sorted_subjects
        }
        selected_subject_display = st.selectbox(
            "Select Subject to Update",
            options=list(subject_options.keys()),
            key="update_subject_select"
        )
        selected_subject_id = subject_options.get(selected_subject_display)

        current_subject_obj = None
        if selected_subject_id is not None:
            current_subject_obj = next((s for s in all_subjects if s['subid'] == selected_subject_id), None)

        if current_subject_obj:
            with st.form("update_subject_form"):
                initial_subname = current_subject_obj['subname']
                initial_level = current_subject_obj['level']
                initial_image_url = current_subject_obj['image_url'] if 'image_url' in current_subject_obj else ''

                updated_subname = st.text_input("New Subject Name", value=initial_subname, key="updated_subject_name_input")
                updated_image_url = st.text_input("New Image URL (optional)", value=initial_image_url, key="updated_subject_image_url_input")
                
                # Level selection for update - only show levels present in milestones
                initial_level_index = 0
                if initial_level in available_levels_for_subjects:
                    initial_level_index = available_levels_for_subjects.index(initial_level)
                elif available_levels_for_subjects:
                    pass # Keep default 0
                else:
                    initial_level_index = -1 # No options available

                updated_level = None
                if available_levels_for_subjects:
                    updated_level = st.selectbox(
                        "New Level",
                        options=available_levels_for_subjects,
                        index=initial_level_index,
                        key="updated_subject_level_select"
                    )
                else:
                    st.info("No valid levels available from milestones to update a subject's level.")


                update_submitted = st.form_submit_button("Update Subject")

                if update_submitted:
                    if selected_subject_id is not None and updated_subname and updated_level:
                        with st.spinner(f"Updating subject ID {selected_subject_id}..."):
                            update_payload = {}
                            if updated_subname != initial_subname:
                                update_payload['subname'] = updated_subname
                            if updated_level != initial_level:
                                update_payload['level'] = updated_level
                            if updated_image_url != initial_image_url:
                                update_payload['image_url'] = updated_image_url
                            
                            # --- Debugging Information (Update Section) ---
                            st.info(f"DEBUG (Update): Selected Subject ID: {selected_subject_id}")
                            st.info(f"DEBUG (Update): Initial Data: Name='{initial_subname}', Level='{initial_level}', Image='{initial_image_url}'")
                            st.info(f"DEBUG (Update): Updated Data: Name='{updated_subname}', Level='{updated_level}', Image='{updated_image_url}'")
                            st.info(f"DEBUG (Update): Payload to send: {update_payload}")
                            # --- End Debugging Information ---

                            if not update_payload:
                                st.info("No changes detected. Subject not updated.")
                                st.rerun()
                                return

                            result = update_subject(selected_subject_id, **update_payload)
                            if result:
                                st.success(f"Subject ID {result['subid']} updated successfully!")
                                st.rerun()
                            else:
                                st.error("Failed to update subject. Please check API logs. This might be due to an invalid level or other backend validation.")
                    else:
                        st.warning("Please select a subject, enter a name, and select a valid level.")
        else:
            st.info("Select a subject from the dropdown to see its details for update.")
    else:
        st.info("No subjects available to update.")

    st.markdown("---") # Separator

    # --- Delete Subject Section ---
    st.subheader("Delete Subject")
    if all_subjects:
        subject_options_delete = {f"ID: {s['subid']} ({s['subname']} - {s['level']})": s['subid'] for s in sorted(all_subjects, key=lambda x: x['subid'])}
        selected_subject_display_delete = st.selectbox(
            "Select Subject to Delete",
            options=list(subject_options_delete.keys()),
            key="delete_subject_select"
        )
        selected_subject_id_delete = subject_options_delete.get(selected_subject_display_delete)

        if st.button("Delete Subject", key="delete_subject_button"):
            if selected_subject_id_delete is not None:
                st.session_state.confirm_delete_subject_id = selected_subject_id_delete
                st.warning(f"Are you sure you want to delete Subject ID: {selected_subject_id_delete}? This will also delete all associated topics. This action cannot be undone.")
            else:
                st.warning("Please select a subject to delete.")
        
        if 'confirm_delete_subject_id' in st.session_state and st.session_state.confirm_delete_subject_id == selected_subject_id_delete:
            if st.button("Confirm Deletion", key="confirm_delete_subject_final_button"):
                with st.spinner(f"Deleting subject ID {selected_subject_id_delete}..."):
                    success = delete_subject(selected_subject_id_delete)
                    if success:
                        st.success(f"Subject ID {selected_subject_id_delete} and associated topics deleted successfully!")
                        del st.session_state.confirm_delete_subject_id
                        st.rerun()
                    else:
                        st.error("Failed to delete subject. Please check API logs.")
    else:
        st.info("No subjects available to delete.")
