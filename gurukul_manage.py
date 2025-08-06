# gurukul_manage.py
import streamlit as st
import requests
import pandas as pd

# Define the base URL for your Node.js API
#API_BASE_URL = "http://localhost:5002"
from config import API_BASE_URL
st.write("Current API URL:", API_BASE_URL)

# --- API Interaction Functions ---

# Function to fetch all gurukuls from the API
def get_all_gurukuls():
    """Fetches all gurukuls from the backend API."""
    try:
        response = requests.get(f"{API_BASE_URL}/gurukul")
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching gurukuls: {e}")
        return []

# Function to create a new gurukul via the API
def create_gurukul(gname):
    """Creates a new gurukul with the given name."""
    try:
        response = requests.post(f"{API_BASE_URL}/gurukul", json={"gname": gname})
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error creating gurukul: {e}")
        return None

# Function to update an existing gurukul via the API
def update_gurukul(gid, gname):
    """Updates an existing gurukul with the given ID and new name."""
    try:
        response = requests.put(f"{API_BASE_URL}/gurukul/{gid}", json={"gname": gname})
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error updating gurukul: {e}")
        return None

# Function to delete a gurukul via the API
def delete_gurukul(gid):
    """Deletes a gurukul with the given ID."""
    try:
        response = requests.delete(f"{API_BASE_URL}/gurukul/{gid}")
        response.raise_for_status()
        return response.status_code == 200 # Check for successful deletion (status 200 OK)
    except requests.exceptions.RequestException as e:
        st.error(f"Error deleting gurukul: {e}")
        return False

# --- Streamlit UI for Gurukul Management ---

def gurukul_manage_page():
    #st.set_page_config(wide="centered") # or "wide" depending on your preference
    col1, col2, col3 = st.columns([1, 1, 1]) # Adjust column ratios if needed
    with col1: # Place content in the first column
        st.image("flower.png", width=50, caption="") # Adjust 'width' for tiny size

    """Renders the UI for managing Gurukuls."""
    st.header("Manage Gurukuls")
    st.write("Here you can create, view, update, and delete Gurukuls.")

    # --- Create Gurukul Section ---
    st.subheader("Create New Gurukul")
    with st.form("create_gurukul_form"):
        new_gurukul_name = st.text_input("Gurukul Name", key="new_gurukul_name_input")
        create_submitted = st.form_submit_button("Create Gurukul")

        if create_submitted:
            if new_gurukul_name:
                with st.spinner("Creating gurukul..."):
                    result = create_gurukul(new_gurukul_name)
                    if result:
                        st.success(f"Gurukul '{result['gname']}' (ID: {result['gid']}) created successfully!")
                        st.rerun() # Rerun to refresh list
                    else:
                        st.error("Failed to create gurukul. Please check API logs.")
            else:
                st.warning("Please enter a gurukul name.")

    st.markdown("---") # Separator

    # --- List Gurukuls Section ---
    st.subheader("Existing Gurukuls")
    gurukuls = get_all_gurukuls()

    if gurukuls:
        # Convert list of dicts to DataFrame for better display
        df_gurukuls = pd.DataFrame(gurukuls)
        st.dataframe(df_gurukuls, use_container_width=True)
    else:
        st.info("No gurukuls found yet.")

    st.markdown("---") # Separator

    # --- Update Gurukul Section ---
    st.subheader("Update Existing Gurukul")
    if gurukuls:
        # Create a dictionary for easy lookup and display in selectbox
        gurukul_options = {f"{g['gname']} (ID: {g['gid']})": g['gid'] for g in gurukuls}
        selected_gurukul_display = st.selectbox(
            "Select Gurukul to Update",
            options=list(gurukul_options.keys()),
            key="update_gurukul_select"
        )

        selected_gurukul_id = gurukul_options.get(selected_gurukul_display)
        
        # Find the currently selected gurukul object to pre-fill its name
        current_gname = ""
        if selected_gurukul_id is not None:
            current_gurukul_obj = next((g for g in gurukuls if g['gid'] == selected_gurukul_id), None)
            if current_gurukul_obj:
                current_gname = current_gurukul_obj['gname']

        with st.form("update_gurukul_form"):
            updated_gurukul_name = st.text_input(
                "New Gurukul Name",
                value=current_gname, # Pre-fill with current name
                key="updated_gurukul_name_input"
            )
            update_submitted = st.form_submit_button("Update Gurukul")

            if update_submitted:
                if selected_gurukul_id is not None and updated_gurukul_name:
                    with st.spinner(f"Updating gurukul ID {selected_gurukul_id}..."):
                        result = update_gurukul(selected_gurukul_id, updated_gurukul_name)
                        if result:
                            st.success(f"Gurukul ID {result['gid']} updated to '{result['gname']}' successfully!")
                            st.rerun() # Rerun to refresh list
                        else:
                            st.error("Failed to update gurukul. Please check API logs.")
                else:
                    st.warning("Please select a gurukul and enter a new name.")
    else:
        st.info("No gurukuls available to update.")

    st.markdown("---") # Separator

    # --- Delete Gurukul Section ---
    st.subheader("Delete Gurukul")
    if gurukuls:
        gurukul_options_delete = {f"{g['gname']} (ID: {g['gid']})": g['gid'] for g in gurukuls}
        selected_gurukul_display_delete = st.selectbox(
            "Select Gurukul to Delete",
            options=list(gurukul_options_delete.keys()),
            key="delete_gurukul_select"
        )

        selected_gurukul_id_delete = gurukul_options_delete.get(selected_gurukul_display_delete)

        if st.button("Delete Gurukul", key="delete_gurukul_button"):
            if selected_gurukul_id_delete is not None:
                # Using a session state variable for confirmation instead of nested buttons,
                # which can cause issues with Streamlit's rerun behavior.
                st.session_state.confirm_delete_gurukul_id = selected_gurukul_id_delete
                st.warning(f"Are you sure you want to delete Gurukul ID: {selected_gurukul_id_delete}? This will also delete all associated offerings. Click 'Confirm Deletion' below to proceed.")
            else:
                st.warning("Please select a gurukul to delete.")
        
        if 'confirm_delete_gurukul_id' in st.session_state and st.session_state.confirm_delete_gurukul_id == selected_gurukul_id_delete:
            if st.button("Confirm Deletion", key="confirm_delete_final_button"):
                with st.spinner(f"Deleting gurukul ID {selected_gurukul_id_delete}..."):
                    success = delete_gurukul(selected_gurukul_id_delete)
                    if success:
                        st.success(f"Gurukul ID {selected_gurukul_id_delete} and its offerings deleted successfully!")
                        del st.session_state.confirm_delete_gurukul_id # Clear confirmation state
                        st.rerun() # Rerun to refresh list
                    else:
                        st.error("Failed to delete gurukul. Please check API logs.")
    else:
        st.info("No gurukuls available to delete.")