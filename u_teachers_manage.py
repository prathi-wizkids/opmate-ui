# u_teachers_manage.py
import streamlit as st
import requests
import pandas as pd

# --- Configuration ---
#API_BASE_URL = "http://localhost:5002" # Your Node.js API URL
from config import API_BASE_URL

# --- API Interaction Functions (Adapted for User API based assignment) ---

def get_all_teachers_from_users():
    """
    Fetches all users with role 'teacher'.
    Assumes backend's /users?role=teacher returns full user objects including 'userid', 'username', 'email', 'user_role_link', and 'assigned_subjects'.
    """
    try:
        response = requests.get(f"{API_BASE_URL}/users?role=teacher")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching teachers: {e}")
        return []

def update_user_with_assignments(userid, updated_subject_ids):
    """
    Sends an update request to the /users/:id endpoint with the new list of subject_ids.
    This replaces all existing assignments for the teacher on the backend.
    """
    payload = {
        "subject_ids": updated_subject_ids
    }
    try:
        response = requests.put(f"{API_BASE_URL}/users/{userid}", json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error updating teacher assignments via /users API: {e}")
        if e.response is not None:
            st.error(f"API Response Status Code: {e.response.status_code}")
            st.error(f"API Response Text: {e.response.text}")
        return None

# --- API Interaction Functions for Subjects (re-used for dropdowns) ---

def get_all_subjects_for_dropdown():
    """Fetches all subjects (subid, subname, level) for use in dropdowns."""
    try:
        response = requests.get(f"{API_BASE_URL}/subjects")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching subjects for dropdown: {e}")
        return []

# --- Streamlit UI for Teacher Assignment Management ---

def u_teachers_manage_page():
    """Renders the UI for managing Teacher Subject Assignments."""
    st.header("Manage Teacher Subject Assignments")
    st.write("Here you can view teachers and their current subject assignments, and manage these assignments.")
    st.info("Note: Subject assignments are managed via the User Update API. All assignments for a teacher are replaced with the new list provided. The 'Is Approver' status is currently set to FALSE by the backend during assignment.")


    all_teachers_general_info = get_all_teachers_from_users() # Get basic teacher user info + assigned_subjects
    all_subjects = get_all_subjects_for_dropdown()
    subject_id_to_details_map = {s['subid']: s for s in all_subjects}

    # Prepare subjects with their levels for selection (only those with a level defined)
    available_subjects_for_assignment_options = []
    for s in all_subjects:
        if s.get('level'):
            display_str = f"{s['subname']} (Level: {s['level']}, ID: {s['subid']})"
            available_subjects_for_assignment_options.append({
                'display': display_str, 
                'subid': s['subid'], 
                'level': s['level'] 
            })
    available_subjects_for_assignment_options.sort(key=lambda x: x['display'])

    if not all_teachers_general_info:
        st.info("No teachers found. Please create users with the 'teacher' role first via 'Manage All Users'.")
        st.markdown("---")
        return

    # --- Display All Teachers with Assignments ---
    st.subheader("All Teachers and Their Assigned Subjects")
    if all_teachers_general_info:
        display_teacher_data = []
        for teacher_user_obj in all_teachers_general_info:
            assigned_subjects_str = "None"
            
            # Use assigned_subjects directly from the teacher_user_obj
            if teacher_user_obj.get('assigned_subjects'):
                assigned_subjects_list = []
                for assignment in teacher_user_obj['assigned_subjects']:
                    subject_info = subject_id_to_details_map.get(assignment['subid']) # Note: 'subid' from userService
                    if subject_info:
                        level_str = f" (Level: {subject_info['level']})" if subject_info.get('level') else ""
                        approver_str = " (Approver)" if assignment.get('isapprover') else "" # Still display if backend provides
                        assigned_subjects_list.append(f"{subject_info['subname']}{level_str}{approver_str}")
                assigned_subjects_str = "; ".join(assigned_subjects_list)
            
            display_teacher_data.append({
                "User ID": teacher_user_obj['userid'],
                "Teacher ID (user_role_link)": teacher_user_obj.get('user_role_link', 'N/A'),
                "Username": teacher_user_obj['username'],
                "Email": teacher_user_obj['email'],
                "Assigned Subjects": assigned_subjects_str
            })
        df_teachers = pd.DataFrame(display_teacher_data)
        st.dataframe(df_teachers, use_container_width=True)
    else:
        st.info("No teachers found yet.")
    
    st.markdown("---")

    # --- Select Teacher for CRUD on Assignments ---
    teacher_options_for_crud = [f"{t['username']} (ID: {t['userid']})" for t in all_teachers_general_info]
    selected_teacher_for_crud_display = st.selectbox(
        "Select Teacher to Manage Assignments For",
        options=teacher_options_for_crud,
        key="select_teacher_for_assignment_crud"
    )
    selected_teacher_user_id_for_crud = int(selected_teacher_for_crud_display.split("(ID: ")[1][:-1]) if selected_teacher_for_crud_display else None
    
    selected_teacher_obj_for_crud = next((t for t in all_teachers_general_info if t['userid'] == selected_teacher_user_id_for_crud), None)
    selected_teachid_for_crud = selected_teacher_obj_for_crud.get('user_role_link') if selected_teacher_obj_for_crud else None

    if not selected_teachid_for_crud:
        st.warning(f"Could not determine teacher's internal ID (teachid) for user '{selected_teacher_obj_for_crud['username'] if selected_teacher_obj_for_crud else 'N/A'}'. Ensure 'user_role_link' is populated for teachers in public.users.")
        st.markdown("---")
        return

    st.markdown(f"**Managing Assignments for: {selected_teacher_obj_for_crud['username']} (Teacher ID: {selected_teachid_for_crud})**")

    # Get the *current* assigned subjects for the selected teacher directly from the fetched user object
    current_assignments_for_selected_teacher = selected_teacher_obj_for_crud.get('assigned_subjects', [])
    current_assigned_subids = {a['subid'] for a in current_assignments_for_selected_teacher}
    
    # Prepare current assigned subjects for pre-selection in multiselect
    current_preselected_subjects_display = []
    for assign in current_assignments_for_selected_teacher:
        subject_info = subject_id_to_details_map.get(assign['subid'])
        if subject_info:
            current_preselected_subjects_display.append(
                f"{subject_info['subname']} (Level: {subject_info['level']}, ID: {subject_info['subid']})"
            )

    st.markdown("---")

    # --- Add/Remove/Update All Assignments in one go Section ---
    st.subheader(f"Update All Subject Assignments (Add/Remove)")
    st.warning("Any changes here will replace ALL existing assignments for this teacher on the backend.")
    st.info("Note: The 'Is Approver' status cannot be controlled from here, as the backend sets it to FALSE upon assignment.")

    with st.form("manage_all_assignments_form"):
        # Display available subjects for multiselect
        # The multiselect options should include all possible subjects with levels
        selected_subjects_for_full_replacement_display = st.multiselect(
            "Select ALL Subjects this Teacher Should Be Assigned To",
            options=[s['display'] for s in available_subjects_for_assignment_options],
            default=current_preselected_subjects_display, # Pre-select current assignments
            key="full_replacement_subjects_multiselect"
        )
        
        # Convert selected display strings back to subids for the payload
        updated_subject_ids_payload = []
        for display_item in selected_subjects_for_full_replacement_display:
            # Find the corresponding subid
            matched_subject = next((s for s in available_subjects_for_assignment_options if s['display'] == display_item), None)
            if matched_subject:
                updated_subject_ids_payload.append(matched_subject['subid'])
        
        # This checkbox is informational, as backend forces FALSE
        st.checkbox("Is Approver (Backend will set to FALSE)", value=False, disabled=True, key="info_approver_checkbox")

        update_all_assignments_submitted = st.form_submit_button("Update All Assignments")

        if update_all_assignments_submitted:
            if selected_teacher_user_id_for_crud is not None:
                with st.spinner(f"Updating all assignments for {selected_teacher_obj_for_crud['username']}..."):
                    # Call the update user API with the full list of subject IDs
                    result = update_user_with_assignments(selected_teacher_user_id_for_crud, updated_subject_ids_payload)
                    if result:
                        st.success(f"All assignments for {selected_teacher_obj_for_crud['username']} updated successfully!")
                        st.rerun() # Rerun to refresh display
                    else:
                        st.error("Failed to update assignments. Please check API logs.")
            else:
                st.warning("Please select a teacher to manage assignments.")
    
    st.markdown("---")

    # --- Display Current Assignments (again, for context after operations) ---
    st.subheader(f"Current Assignments for {selected_teacher_obj_for_crud['username']} (After Update)")
    # Re-fetch or re-use the updated data for display if needed, for simplicity let's re-fetch
    # This also helps confirm the backend changes
    updated_teacher_info = next((t for t in get_all_teachers_from_users() if t['userid'] == selected_teacher_user_id_for_crud), None)
    if updated_teacher_info and updated_teacher_info.get('assigned_subjects'):
        display_assignments_after_update = []
        for assign in updated_teacher_info['assigned_subjects']:
            subject_details = subject_id_to_details_map.get(assign['subid'])
            subname = subject_details['subname'] if subject_details else "N/A"
            level = subject_details['level'] if subject_details and subject_details.get('level') else "N/A"
            display_assignments_after_update.append({
                "Subject Name": subname,
                "Level": level,
                "Subject ID": assign['subid'],
                "Is Approver": "Yes" if assign.get('isapprover') else "No"
            })
        df_assignments_after_update = pd.DataFrame(display_assignments_after_update)
        st.dataframe(df_assignments_after_update, use_container_width=True)
    else:
        st.info(f"{selected_teacher_obj_for_crud['username']} has no subjects assigned yet (or after the update).")

