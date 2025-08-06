# DirectStudent_manage.py - Fix for IndexError

import streamlit as st
import requests
import json
import re # Import regex for parsing IDs from display strings

# --- Configuration ---
API_BASE_URL = "http://localhost:5002"

# --- API Interaction Functions ---

def direct_api_call(method, endpoint, payload=None):
    url = f"{API_BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    
    try:
        # st.markdown(f"**DEBUG API CALL:** Method={method}, Endpoint={endpoint}, Payload={payload}")
        print(f"DEBUG API CALL: Method={method}, Endpoint={endpoint}, Payload={payload}")
        if method == 'GET':
            response = requests.get(url, headers=headers)
        elif method == 'POST':
            response = requests.post(url, headers=headers, data=json.dumps(payload))
        elif method == 'PUT':
            response = requests.put(url, headers=headers, data=json.dumps(payload))
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers)
        else:
            return 400, {"message": "Unsupported HTTP method"}

        if response.status_code == 204:
            # st.markdown(f"**DEBUG API RESPONSE:** Status=204 (No Content) for {endpoint}")
            print(f"DEBUG API RESPONSE: Status=204 (No Content) for {endpoint}")
            return response.status_code, {}

        try:
            data = response.json()
            # st.markdown(f"**DEBUG API RESPONSE:** Status={response.status_code}, Data={data} for {endpoint}")
            print(f"DEBUG API RESPONSE: Status={response.status_code}, Data={data} for {endpoint}")
        except json.JSONDecodeError:
            # st.markdown(f"**DEBUG: JSONDecodeError** for {method} {url}. Raw response content: '{response.text}'")
            print(f"DEBUG: JSONDecodeError for {method} {url}. Raw response content: '{response.text}'")
            return response.status_code, {"message": f"Invalid JSON response from API: {response.text}"}

        return response.status_code, data

    except requests.exceptions.ConnectionError:
        st.error(f"Failed to connect to API at {API_BASE_URL}. Please ensure the backend server is running.")
        # st.markdown(f"**ERROR: ConnectionError** to API at {API_BASE_URL}")
        print(f"ERROR: ConnectionError to API at {API_BASE_URL}")
        return 503, {"message": "API service unavailable"}
    except requests.exceptions.Timeout:
        st.error("API request timed out.")
        # st.markdown("**ERROR: API request timed out.**")
        print("ERROR: API request timed out.")
        return 408, {"message": "API request timed out"}
    except requests.exceptions.RequestException as e:
        st.error(f"An unexpected error occurred during API request: {e}")
        # st.markdown(f"**ERROR: Unexpected API request error:** {e}")
        print(f"ERROR: Unexpected API request error: {e}")
        return 500, {"message": f"API request error: {e}"}


@st.cache_data(ttl=60)
def fetch_all_students_direct():
    status, data = direct_api_call('GET', '/students')
    if status == 200:
        return data
    st.error(f"Failed to fetch students directly: {data.get('message', 'Unknown error')}")
    return []

@st.cache_data(ttl=60)
def fetch_all_gurukuls():
    status, data = direct_api_call('GET', '/gurukul')
    if status == 200:
        return data
    st.error(f"Failed to fetch gurukuls: {data.get('message', 'Unknown error')}")
    return []

@st.cache_data(ttl=60)
def fetch_milestones_by_gurukul(gid):
    if gid is None:
        return []
    status, data = direct_api_call('GET', f'/milestones/by-gurukul/{gid}')
    if status == 200:
        return data
    st.error(f"Failed to fetch milestones for Gurukul ID {gid}: {data.get('message', 'Unknown error')}")
    return []

@st.cache_data(ttl=60)
def fetch_all_milestones():
    status, data = direct_api_call('GET', '/milestones')
    if status == 200:
        return data
    st.error(f"Failed to fetch all milestones: {data.get('message', 'Unknown error')}")
    return []

@st.cache_data(ttl=60)
def fetch_all_offerings():
    status, data = direct_api_call('GET', '/gurukul-offerings')
    if status == 200:
        return data
    st.error(f"Failed to fetch all offerings: {data.get('message', 'Unknown error')}")
    return []


def initialize_direct_student_crud_states():
    # Add form states for new student
    if 'direct_add_student_name_input_val' not in st.session_state:
        st.session_state.direct_add_student_name_input_val = ""
    if 'direct_add_student_email_input_val' not in st.session_state:
        st.session_state.direct_add_student_email_input_val = "" 
    if 'direct_selected_add_student_gurukul_name' not in st.session_state:
        st.session_state.direct_selected_add_student_gurukul_name = ""
    if 'direct_selected_add_student_gurukul_id' not in st.session_state:
        st.session_state.direct_selected_add_student_gurukul_id = None
    if 'direct_selected_add_student_milestone_name' not in st.session_state:
        st.session_state.direct_selected_add_student_milestone_name = "-- Select Milestone --"
    if 'direct_selected_add_student_milestone_id' not in st.session_state:
        st.session_state.direct_selected_add_student_milestone_id = None

    # Update form states (these will be set when a student is selected)
    # These are for the text inputs, not the selectboxes, as selectbox values
    # will be handled by local variables and then processed on button click.
    if 'direct_update_student_name_input_val' not in st.session_state:
        st.session_state.direct_update_student_name_input_val = ""
    if 'direct_update_student_email_input_val' not in st.session_state:
        st.session_state.direct_update_student_email_input_val = ""
    
    # Flag to control initial loading of update form input values
    if 'update_form_loaded_student_id' not in st.session_state:
        st.session_state.update_form_loaded_student_id = None


def on_direct_add_gurukul_change():
    all_gurukuls = fetch_all_gurukuls()
    gurukul_options = {g['gname']: g['gid'] for g in all_gurukuls}
    st.session_state.direct_selected_add_student_gurukul_id = gurukul_options.get(st.session_state.direct_selected_add_student_gurukul_name)
    
    st.session_state.direct_selected_add_student_milestone_name = "-- Select Milestone --"
    st.session_state.direct_selected_add_student_milestone_id = None
    st.cache_data.clear()


def on_direct_add_milestone_change():
    current_gurukul_id = st.session_state.get('direct_selected_add_student_gurukul_id')
    milestones_for_selected_gurukul = []
    if current_gurukul_id is not None:
        milestones_for_selected_gurukul = fetch_milestones_by_gurukul(current_gurukul_id)

    milestone_options_filtered = {"-- Select Milestone --": None}
    milestone_options_filtered.update({
        f"Level {m['level']} (Class: {m['class']}, ID: {m['mid']})": m['mid']
        for m in milestones_for_selected_gurukul
    })
    st.session_state.direct_selected_add_student_milestone_id = milestone_options_filtered.get(st.session_state.direct_selected_add_student_milestone_name)


def show_student_crud_direct():
    st.header("Manage Students (Direct)")
    st.info("This section allows you to manage student users directly via the /students endpoint.")

    initialize_direct_student_crud_states()

    st.subheader("Add New Student")
    all_gurukuls = fetch_all_gurukuls()
    all_offerings = fetch_all_offerings() # Fetch all offerings
    all_milestones = fetch_all_milestones() # Fetch all milestones

    # Create maps for easy lookup for the filtering logic
    offering_id_to_details_map = {o['oid']: o for o in all_offerings}

    # Determine which Gurukuls have at least one associated Milestone
    gids_with_milestones = set()
    for milestone in all_milestones:
        offering_details = offering_id_to_details_map.get(milestone['oid'])
        if offering_details and offering_details.get('gid'):
            gids_with_milestones.add(offering_details['gid'])
    
    # Filter gurukuls to only include those that have associated milestones
    filtered_gurukuls_with_milestones = [
        g for g in all_gurukuls if g['gid'] in gids_with_milestones
    ]

    if not filtered_gurukuls_with_milestones: # Use the filtered list here
        st.warning("No Gurukuls with associated Milestones found. Please add Gurukuls and Milestones first to assign to students.")
        with st.form("add_student_direct_form_disabled", clear_on_submit=True):
            st.text_input("Student Name", key="direct_add_student_username_input_disabled", disabled=True)
            st.text_input("Student Email", key="direct_add_student_email_input_disabled", disabled=True)
            st.selectbox("Assign to Gurukul (Mandatory)", ["No Gurukuls Available"], disabled=True)
            st.selectbox("Assign to Milestone (Optional)", ["No Milestones Available"], disabled=True)
            st.form_submit_button("Add Student", disabled=True)
        return

    gurukul_options = {g['gname']: g['gid'] for g in filtered_gurukuls_with_milestones} # Use filtered list
    gurukul_names = [g['gname'] for g in filtered_gurukuls_with_milestones] # Use filtered list

    new_student_name_input = st.text_input("Student Name", key="direct_add_student_name_input_add_form")
    new_student_email_input = st.text_input("Student Email", key="direct_add_student_email_input_add_form")

    current_gurukul_index = 0
    if st.session_state.direct_selected_add_student_gurukul_name in gurukul_names:
        current_gurukul_index = gurukul_names.index(st.session_state.direct_selected_add_student_gurukul_name)

    selected_gurukul_name_add_form_current = st.selectbox(
        "Assign to Gurukul (Mandatory)",
        gurukul_names,
        key="direct_selected_add_student_gurukul_name",
        index=current_gurukul_index,
        on_change=on_direct_add_gurukul_change
    )
    st.session_state.direct_selected_add_student_gurukul_id = gurukul_options.get(selected_gurukul_name_add_form_current)


    gurukul_id_for_milestone_filter = st.session_state.get('direct_selected_add_student_gurukul_id')
    milestones_for_selected_gurukul = []
    if gurukul_id_for_milestone_filter is not None:
        milestones_for_selected_gurukul = fetch_milestones_by_gurukul(gurukul_id_for_milestone_filter)
    
    milestone_options_filtered = {"-- Select Milestone --": None}
    milestone_options_filtered.update({
        f"Level {m['level']} (Class: {m['class']}, ID: {m['mid']})": m['mid']
        for m in milestones_for_selected_gurukul
    })
    milestone_names_filtered = list(milestone_options_filtered.keys())

    current_milestone_index = 0
    if st.session_state.direct_selected_add_student_milestone_name in milestone_names_filtered:
        current_milestone_index = milestone_names_filtered.index(st.session_state.direct_selected_add_student_milestone_name)
    else:
        st.session_state.direct_selected_add_student_milestone_name = "-- Select Milestone --"
        current_milestone_index = 0

    selected_milestone_name_add_form_current = st.selectbox(
        "Assign to Milestone (Optional)",
        milestone_names_filtered,
        key="direct_selected_add_student_milestone_name",
        index=current_milestone_index,
        disabled=(gurukul_id_for_milestone_filter is None or not milestones_for_selected_gurukul),
        on_change=on_direct_add_milestone_change
    )
    st.session_state.direct_selected_add_student_milestone_id = milestone_options_filtered.get(selected_milestone_name_add_form_current)


    with st.form("add_student_direct_submit_form", clear_on_submit=True):
        submit_add_student = st.form_submit_button("Add Student")

        if submit_add_student:
            if not new_student_name_input or not new_student_email_input:
                st.warning("Please enter student name and email.")
            elif st.session_state.direct_selected_add_student_gurukul_id is None:
                st.warning("Please select a Gurukul. It is mandatory.")
            else:
                payload = {
                    'sname': new_student_name_input,
                    'email': new_student_email_input,
                    'gurukulId': st.session_state.direct_selected_add_student_gurukul_id,
                    'milestoneId': st.session_state.direct_selected_add_student_milestone_id
                }
                print(f"DEBUG: Sending add student payload: {payload}")
                status, data = direct_api_call('POST', '/students', payload)
                if status == 201:
                    st.success(f"Student '{new_student_name_input}' added successfully!")
                    st.cache_data.clear()
                    st.rerun()
                elif status == 409:
                    st.warning(f"Failed to add student: User with email '{new_student_email_input}' already exists.")
                else:
                    st.error(f"Failed to add student: {data.get('message', 'Unknown error')}")
    st.subheader("Existing Students")
    students = fetch_all_students_direct()
    # ### DEBUG: Added debug print for raw fetched students data (UI and console)
    #st.markdown(f"**DEBUG (Raw Student Data from /students endpoint):** {json.dumps(students, indent=2)}")
    print(f"DEBUG: Fetched existing students (raw data): {json.dumps(students, indent=2)}")
    if not students:
        st.info("No Students found. Add one above!")
    else:
        # ### CHANGE START: Fetch all milestones once for lookup in display table
        # This is crucial because assigned_milestones from /students endpoint likely only contain MIDs, not full details.
        all_milestones_fetched_for_display = fetch_all_milestones()
        milestone_id_to_obj_map_for_display = {m['mid']: m for m in all_milestones_fetched_for_display}
        # ### CHANGE END: Fetch all milestones once for lookup in display table
        students_display_data = []
        for student in students:
            assigned_gurukuls_formatted = ", ".join([g['gname'] for g in student.get('assigned_gurukuls', [])])
            if not assigned_gurukuls_formatted:
                assigned_gurukuls_formatted = "N/A"
            # ### CHANGE START: Corrected logic to format assigned milestones using lookup
            assigned_milestones_formatted_list = []
            # Iterate over the assigned_milestones references (which contain 'mid')
            for assigned_m_ref in student.get('assigned_milestones', []):
                milestone_id = assigned_m_ref.get('mid') # Get the milestone ID from the reference object
                if milestone_id:
                    # Lookup full details using the map created from all milestones
                    full_milestone_details = milestone_id_to_obj_map_for_display.get(milestone_id)
                    if full_milestone_details:
                        # Ensure 'level' and 'class' keys exist in the full details
                        level = full_milestone_details.get('level', 'N/A')
                        class_val = full_milestone_details.get('class', 'N/A')
                        assigned_milestones_formatted_list.append(
                            f"Level {level} (Class {class_val})"
                        )
            assigned_milestones_formatted = ", ".join(assigned_milestones_formatted_list)
            if not assigned_milestones_formatted:
                assigned_milestones_formatted = "N/A"
            # ### CHANGE END: Corrected logic to format assigned milestones using lookup
            students_display_data.append({
                'SID': student['sid'],
                'Name': student['sname'],
                'Email': student['email'],
                'Assigned Gurukuls': assigned_gurukuls_formatted,
                'Assigned Milestones': assigned_milestones_formatted
            })
        st.dataframe(students_display_data, use_container_width=True)
        student_options = {f"{u['sname']} (ID: {u['sid']})": u['sid'] for u in students}
        selected_student_display = st.selectbox(
            "Select Student to Update/Delete",
            options=["-- Select Student --"] + list(student_options.keys()),
            key="selected_student_for_crud"
        )

        st.session_state.selected_student_id = student_options.get(selected_student_display)
        
        # --- Update/Delete Section ---
        if st.session_state.selected_student_id:
            st.markdown("---")
            st.subheader(f"Update/Delete Student (ID: {st.session_state.selected_student_id})")
            
            selected_student_obj = next((s for s in students if s['sid'] == st.session_state.selected_student_id), None)

            if selected_student_obj:
                # Initialize update form text inputs only once when a new student is selected
                if st.session_state.update_form_loaded_student_id != st.session_state.selected_student_id:
                    st.session_state.direct_update_student_name_input_val = selected_student_obj.get('sname', '')
                    st.session_state.direct_update_student_email_input_val = selected_student_obj.get('email', '')
                    st.session_state.update_form_loaded_student_id = st.session_state.selected_student_id

                updated_name = st.text_input("Student Name", value=st.session_state.direct_update_student_name_input_val, key=f"update_name_{st.session_state.selected_student_id}")
                updated_email = st.text_input("Student Email", value=st.session_state.direct_update_student_email_input_val, key=f"update_email_{st.session_state.selected_student_id}")

                # --- Gurukul and Milestone Assignment for Update ---
                current_assigned_gurukul_id = selected_student_obj.get('gurukulId')
                current_assigned_milestone_id = selected_student_obj.get('milestoneId')

                # Determine the currently assigned gurukul name for the selectbox default
                current_gurukul_name = "None (Unassign Gurukul)"
                if current_assigned_gurukul_id:
                    current_gurukul_obj = next((g for g in filtered_gurukuls_with_milestones if g['gid'] == current_assigned_gurukul_id), None) # Use filtered list
                    if current_gurukul_obj:
                        current_gurukul_name = current_gurukul_obj['gname']

                # Create options for Gurukul dropdown, including "None"
                gurukul_options_for_update_select = ["None (Unassign Gurukul)"] + [g['gname'] for g in filtered_gurukuls_with_milestones] # Use filtered list
                try:
                    default_gurukul_index = gurukul_options_for_update_select.index(current_gurukul_name)
                except ValueError:
                    default_gurukul_index = 0 # Default to "None" if current gurukul not in options

                selected_gurukul_name_update_form = st.selectbox(
                    "Assign/Reassign Gurukul",
                    options=gurukul_options_for_update_select,
                    index=default_gurukul_index,
                    key=f"update_gurukul_select_{st.session_state.selected_student_id}"
                )

                # Convert selected gurukul name back to ID
                final_gurukul_id_to_send = None
                if selected_gurukul_name_update_form != "None (Unassign Gurukul)":
                    final_gurukul_id_to_send = next(
                        (g['gid'] for g in filtered_gurukuls_with_milestones if g['gname'] == selected_gurukul_name_update_form), None # Use filtered list
                    )

                # --- Milestone selection for Update ---
                milestones_for_update_gurukul = []
                if final_gurukul_id_to_send:
                    milestones_for_update_gurukul = fetch_milestones_by_gurukul(final_gurukul_id_to_send)

                current_milestone_name = "None (Unassign Milestone)"
                if current_assigned_milestone_id:
                    current_milestone_obj = next(
                        (m for m in milestones_for_update_gurukul if m['mid'] == current_assigned_milestone_id), None
                    )
                    if current_milestone_obj:
                        current_milestone_name = f"Level {current_milestone_obj['level']} (Class: {current_milestone_obj['class']}, ID: {current_milestone_obj['mid']})"

                milestone_options_for_update_select = ["None (Unassign Milestone)"] + [
                    f"Level {m['level']} (Class: {m['class']}, ID: {m['mid']})"
                    for m in milestones_for_update_gurukul
                ]
                
                try:
                    default_milestone_index = milestone_options_for_update_select.index(current_milestone_name)
                except ValueError:
                    default_milestone_index = 0 # Default to "None" if current milestone not in options

                selected_milestone_name_update_form = st.selectbox(
                    "Assign/Reassign Milestone",
                    options=milestone_options_for_update_select,
                    index=default_milestone_index,
                    key=f"update_milestone_select_{st.session_state.selected_student_id}",
                    disabled=(final_gurukul_id_to_send is None or not milestones_for_update_gurukul)
                )

                final_milestone_id_to_send = None
                if selected_milestone_name_update_form != "None (Unassign Milestone)":
                    match = re.search(r"ID: (\d+)", selected_milestone_name_update_form)
                    if match:
                        final_milestone_id_to_send = int(match.group(1))

                # --- Debugging (Optional, can be removed in final version) ---
                print(f"CONSOLE DEBUG (Update Button Click): Final Gurukul ID to send: {final_gurukul_id_to_send}")
                print(f"CONSOLE DEBUG (Update Button Click): Final Milestone ID to send: {final_milestone_id_to_send}")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Update Student", key=f"update_student_btn_{st.session_state.selected_student_id}"):
                        if not updated_name or not updated_email:
                            st.warning("Student name and email cannot be empty.")
                        else:
                            update_payload = {
                                'sname': updated_name,
                                'email': updated_email,
                                'gurukulId': final_gurukul_id_to_send,
                                'milestoneId': final_milestone_id_to_send
                            }
                            print(f"DEBUG: Sending update student payload for SID {st.session_state.selected_student_id}: {update_payload}")
                            status, data = direct_api_call('PUT', f'/students/{st.session_state.selected_student_id}', update_payload)
                            if status == 200:
                                st.success(f"Student '{updated_name}' updated successfully!")
                                st.cache_data.clear()
                                st.session_state.update_form_loaded_student_id = None # Reset flag to re-initialize on next selection
                                st.rerun()
                            elif status == 409:
                                st.warning(f"Failed to update student: User with email '{updated_email}' already exists.")
                            else:
                                st.error(f"Failed to update student: {data.get('message', 'Unknown error')}")
                with col2:
                    if st.button("Delete Student", key=f"delete_student_btn_{st.session_state.selected_student_id}"):
                        if st.session_state.selected_student_id:
                            status, data = direct_api_call('DELETE', f'/students/{st.session_state.selected_student_id}')
                            if status == 204:
                                st.success(f"Student (ID: {st.session_state.selected_student_id}) deleted successfully!")
                                st.cache_data.clear()
                                st.session_state.selected_student_id = None # Clear selection after deletion
                                st.rerun()
                            else:
                                st.error(f"Failed to delete student: {data.get('message', 'Unknown error')}")
            else:
                st.warning("Selected student details not found.")
