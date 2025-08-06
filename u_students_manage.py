# u_students_manage.py
import streamlit as st
import requests
import pandas as pd
import re # Import the regular expression module

# --- Configuration ---
#API_BASE_URL = "http://localhost:5002" # Your Node.js API URL
from config import API_BASE_URL

# --- API Interaction Functions for Students (via Users API) ---

def get_all_students_from_users():
    """
    Fetches all users with role 'student'.
    Assumes backend's /users?role=student returns full user objects including 'userid', 'username', 'email', 'user_role_link', and assigned_gurukuls/milestones.
    """
    try:
        response = requests.get(f"{API_BASE_URL}/users?role=student")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching students: {e}")
        print(f"ERROR: get_all_students_from_users failed: {e}") # Console log
        if e.response is not None:
            print(f"API Response Status Code: {e.response.status_code}")
            print(f"API Response Text: {e.response.text}")
        return []

def update_user_student_assignments(userid, gurukul_id=None, milestone_id=None):
    """
    Sends an update request to the /users/:id endpoint with the new gurukul_id or milestone_id.
    The backend's userService will handle the assignment logic (deleting existing and inserting new).
    """
    payload = {}
    # Ensure None is passed explicitly for unassignment, but only include if relevant
    if gurukul_id is not None:
        payload["gurukul_id"] = gurukul_id
    elif gurukul_id is None: # If explicit unassign requested for gurukul
        payload["gurukul_id"] = None

    if milestone_id is not None:
        payload["milestone_id"] = milestone_id
    elif milestone_id is None: # If explicit unassign requested for milestone
        payload["milestone_id"] = None
    
    if not payload:
        st.warning("No Gurukul or Milestone provided for update.")
        return None

    # --- Debugging API Request Payload (Console and UI Expander) ---
    print(f"DEBUG (update_user_student_assignments): Sending payload for user {userid}: {payload}") # Console log
    with st.expander("API Request Debug Info"):
        st.write(f"Sending payload for user {userid}:")
        st.json(payload)
    # --- End Debugging API Request Payload ---

    try:
        response = requests.put(f"{API_BASE_URL}/users/{userid}", json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error updating student assignments via /users API: {e}")
        print(f"ERROR: update_user_student_assignments failed: {e}") # Console log
        if e.response is not None:
            print(f"API Response Status Code: {e.response.status_code}")
            print(f"API Response Text: {e.response.text}")
        return None

# --- API Interaction Functions for Gurukuls, Offerings, Milestones (for dropdowns) ---

def get_all_gurukuls_api():
    """Fetches all gurukuls from the backend API."""
    try:
        response = requests.get(f"{API_BASE_URL}/gurukul")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching gurukuls: {e}")
        print(f"ERROR: get_all_gurukuls_api failed: {e}") # Console log
        return []

def get_all_gurukul_offerings_api():
    """Fetches all gurukul offerings from the backend API."""
    try:
        response = requests.get(f"{API_BASE_URL}/gurukul-offerings")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching gurukul offerings: {e}")
        print(f"ERROR: get_all_gurukul_offerings_api failed: {e}") # Console log
        return []

def get_all_milestones_api():
    """Fetches all milestones from the backend API."""
    try:
        response = requests.get(f"{API_BASE_URL}/milestones")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching milestones: {e}")
        print(f"ERROR: get_all_milestones_api failed: {e}") # Console log
        return []

# --- Streamlit UI for Student Assignment Management ---

def u_students_manage_page():
    """Renders the UI for managing Student Gurukul and Milestone Assignments."""
    st.header("Manage Student Gurukul and Milestone Assignments")
    st.write("Assign and update Gurukuls and Milestones for students.")
    st.info("Note: Assigning a new Gurukul or Milestone will replace any existing assignment of that type for the student.")

    all_students = get_all_students_from_users()
    all_gurukuls = get_all_gurukuls_api()
    all_offerings = get_all_gurukul_offerings_api()
    all_milestones = get_all_milestones_api()

    # Create maps for easy lookup
    gurukul_id_to_name_map = {g['gid']: g['gname'] for g in all_gurukuls}
    offering_id_to_details_map = {o['oid']: o for o in all_offerings}
    milestone_id_to_details_map = {m['mid']: m for m in all_milestones}

    if not all_students:
        st.info("No students found. Please create users with the 'student' role first via 'Manage All Users'.")
        st.markdown("---")
        return

    # --- Select Student ---
    student_options = [f"{s['username']} (ID: {s['userid']})" for s in all_students]
    selected_student_display = st.selectbox(
        "Select Student to Manage Assignments For",
        options=student_options,
        key="select_student_for_assignment_crud"
    )
    selected_student_user_id = int(selected_student_display.split("(ID: ")[1][:-1]) if selected_student_display else None
    
    selected_student_obj = next((s for s in all_students if s['userid'] == selected_student_user_id), None)
    selected_sid = selected_student_obj.get('user_role_link') if selected_student_obj else None

    if not selected_sid:
        st.warning(f"Could not determine student's internal ID (sid) for user '{selected_student_obj['username'] if selected_student_obj else 'N/A'}'. Ensure 'user_role_link' is populated for students in public.users.")
        st.markdown("---")
        return

    st.markdown(f"**Managing Assignments for: {selected_student_obj['username']} (Student ID: {selected_sid})**")
    st.markdown("---")

    # --- Display Current Assignments (FROZEN LOGIC) ---
    st.subheader("Current Assignments")
    current_assigned_gurukuls = selected_student_obj.get('assigned_gurukuls', [])
    current_assigned_milestones = selected_student_obj.get('assigned_milestones', [])

    if current_assigned_gurukuls:
        st.write("**:mortar_board: Assigned Gurukul:**")
        df_gurukul = pd.DataFrame(current_assigned_gurukuls)
        st.dataframe(df_gurukul[['gname', 'starttime', 'status']], use_container_width=True)
    else:
        st.info("No Gurukul assigned.")

    if current_assigned_milestones:
        st.write("**:books: Assigned Milestones:**")
        df_milestones = pd.DataFrame(current_assigned_milestones)
        st.dataframe(df_milestones[['class', 'level', 'starttime', 'status', 'score']], use_container_width=True)
    else:
        st.info("No Milestones assigned.")
    
    st.markdown("---")

    # --- Assign/Update Gurukul & Milestone (Combined Section) ---
    st.subheader("Assign/Update Gurukul & Milestone")
    
    if not all_gurukuls or not all_offerings or not all_milestones:
        st.info("Not all necessary data (Gurukuls, Offerings, Milestones) is available. Please ensure they are created in their respective management pages.")
    else:
        # Determine which Gurukuls have at least one associated Milestone
        gids_with_milestones = set()
        for milestone in all_milestones:
            offering_details = offering_id_to_details_map.get(milestone['oid'])
            if offering_details and offering_details['gid']:
                gids_with_milestones.add(offering_details['gid'])
        
        filtered_gurukuls_with_milestones = [
            g for g in all_gurukuls if g['gid'] in gids_with_milestones
        ]

        if not filtered_gurukuls_with_milestones:
            st.info("No Gurukuls found that have associated Milestones. Cannot assign a Gurukul-Milestone pair.")
        else:
            # Prepare Gurukul options, including 'None (Unassign)'
            gurukul_options_with_none = ["None (Unassign Gurukul)"] + sorted(
                [f"{g['gname']} (ID: {g['gid']})" for g in filtered_gurukuls_with_milestones]
            )
            
            selected_gurukul_display = st.selectbox( # Use a consistent variable name
                "Select Gurukul",
                options=gurukul_options_with_none,
                key="assign_gurukul_combined_select"
            )
            
            print(f"CONSOLE DEBUG: Selected Gurukul Display (from selectbox): '{selected_gurukul_display}'") # Console log

            # Initialize these to None. Their values will be set conditionally below.
            selected_offering_display = None
            selected_milestone_display = None


            # Conditional display for Offering and Milestone based on Gurukul selection
            if selected_gurukul_display != "None (Unassign Gurukul)":
                # Filter Offerings by Selected Gurukul
                selected_gurukul_id_for_filters = int(selected_gurukul_display.split("(ID: ")[1][:-1])

                filtered_offerings_for_selected_gurukul = [
                    o for o in all_offerings if o['gid'] == selected_gurukul_id_for_filters
                ]
                offering_options_for_milestone = [f"{o['gtype']} (OID: {o['oid']})" for o in filtered_offerings_for_selected_gurukul]
                
                if not offering_options_for_milestone:
                    st.info(f"No Offerings found for Gurukul '{selected_gurukul_display}'.")
                else:
                    selected_offering_display = st.selectbox(
                        "Select Offering",
                        options=offering_options_for_milestone,
                        key="assign_offering_combined_select"
                    )
                    print(f"CONSOLE DEBUG: Selected Offering Display (from selectbox): '{selected_offering_display}'") # Console log

                    # Filter Milestones by Selected Offering
                    if selected_offering_display is not None:
                        selected_offering_id_for_filters = int(selected_offering_display.split("(OID: ")[1][:-1])

                        filtered_milestones_for_selected_offering = [
                            m for m in all_milestones if m['oid'] == selected_offering_id_for_filters
                        ]
                    else: # No offering selected, so no milestones
                        filtered_milestones_for_selected_offering = []
                    
                    milestone_options_with_none = ["None (Unassign Milestone)"] + sorted(
                        [f"{m['class']} (Level: {m['level']}, MID: {m['mid']})" for m in filtered_milestones_for_selected_offering]
                    )

                    selected_milestone_display = st.selectbox(
                        "Select Milestone",
                        options=milestone_options_with_none,
                        key="assign_milestone_combined_select"
                    )
                    print(f"CONSOLE DEBUG: Selected Milestone Display: '{selected_milestone_display}'") # Console log
            
            # --- Button Click Logic ---
            if st.button("Assign Gurukul & Milestone", key="assign_gurukul_milestone_button"):
                final_gurukul_id_to_send = None
                final_milestone_id_to_send = None

                # Parse Gurukul ID from the selected display string
                if selected_gurukul_display != "None (Unassign Gurukul)":
                    if selected_gurukul_display and "(ID: " in selected_gurukul_display:
                        final_gurukul_id_to_send = int(selected_gurukul_display.split("(ID: ")[1][:-1])
                    else:
                        st.error(f"Error parsing Gurukul ID: Unexpected format '{selected_gurukul_display}'")
                        st.stop() # Stop execution to prevent further errors
                
                # Parse Milestone ID from the selected display string, but only if an offering was also selected.
                # Use the local variable selected_offering_display (which might be None)
                if selected_offering_display is not None and selected_offering_display != "None (Unassign Offering)": 
                    if selected_milestone_display is not None and selected_milestone_display != "None (Unassign Milestone)":
                        try:
                            # Use regex to extract the MID value
                            match = re.search(r"MID:\s*(\d+)", selected_milestone_display)
                            if match:
                                milestone_id_str = match.group(1)
                                final_milestone_id_to_send = int(milestone_id_str)
                            else:
                                st.error(f"Error parsing Milestone ID: Cannot find expected 'MID: <number>' format in '{selected_milestone_display}'")
                                st.stop()
                        except ValueError:
                            st.error(f"Error parsing Milestone ID: Could not convert '{milestone_id_str}' to integer.")
                            st.stop()
                    else:
                        final_milestone_id_to_send = None # User explicitly selected None for milestone

                # --- Debugging values before API call ---
                print(f"CONSOLE DEBUG (Assign Button Click): Final Gurukul ID to send: {final_gurukul_id_to_send}") # Console log
                print(f"CONSOLE DEBUG (Assign Button Click): Final Milestone ID to send: {final_milestone_id_to_send}") # Console log
                with st.expander("Final Assignment Values (Before API Call)"):
                    st.write(f"Gurukul ID: {final_gurukul_id_to_send}")
                    st.write(f"Milestone ID: {final_milestone_id_to_send}")
                # --- End Debugging ---

                # Handle assignment/unassignment logic
                if final_gurukul_id_to_send is None and final_milestone_id_to_send is None:
                    st.warning("Please select a Gurukul and Milestone, or 'None' for both to unassign.")
                else:
                    with st.spinner(f"Updating assignments for {selected_student_obj['username']}..."):
                        result = update_user_student_assignments(
                            selected_student_user_id,
                            gurukul_id=final_gurukul_id_to_send,
                            milestone_id=final_milestone_id_to_send
                        )
                        if result:
                            st.success(f"Gurukul and Milestone assignments updated successfully for {selected_student_obj['username']}!")
                            st.rerun() # Rerun to refresh display
                        else:
                            st.error("Failed to update assignments. Please check API logs.")

