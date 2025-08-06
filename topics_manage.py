# topics_manage.py
import streamlit as st
import requests
import pandas as pd
import re # Import regex for parsing IDs from display strings

# --- Configuration ---
#API_BASE_URL = "http://localhost:5002" # Your Node.js API URL
from config import API_BASE_URL

# --- API Interaction Functions for Topics ---

def get_all_topics():
    """Fetches all topics from the backend API."""
    try:
        response = requests.get(f"{API_BASE_URL}/topics")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching topics: {e}")
        return []

def create_topic(tname, subid, image_url):
    """Creates a new topic."""
    try:
        payload = {"tname": tname, "subid": subid}
        if image_url:
            payload["image_url"] = image_url
        response = requests.post(f"{API_BASE_URL}/topics", json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error creating topic: {e}")
        return None

def update_topic(tid, tname=None, subid=None, image_url=None):
    """Updates an existing topic."""
    payload = {}
    if tname is not None:
        payload["tname"] = tname
    if subid is not None:
        payload["subid"] = subid
    if image_url is not None: # Allow updating to empty string
        payload["image_url"] = image_url
    
    try:
        response = requests.put(f"{API_BASE_URL}/topics/{tid}", json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error updating topic: {e}")
        return None

def delete_topic(tid):
    """Deletes a topic."""
    try:
        response = requests.delete(f"{API_BASE_URL}/topics/{tid}")
        response.raise_for_status()
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        st.error(f"Error deleting topic: {e}")
        return False

# --- API Interaction Functions for Subjects (re-used) ---

def get_all_subjects_for_dropdown():
    """Fetches all subjects (subid, subname, level) for use in dropdowns.
       Assumes the /subjects endpoint returns 'level' field."""
    try:
        response = requests.get(f"{API_BASE_URL}/subjects")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching subjects for dropdown: {e}")
        return []

# --- Streamlit UI for Topic Management ---

def topics_manage_page():
    """Renders the UI for managing Topics."""
    st.header("Manage Topics")
    st.write("Here you can create, view, update, and delete Topics.")

    # Fetch all necessary data
    all_topics = get_all_topics()
    all_subjects = get_all_subjects_for_dropdown()

    # Create maps for easy lookup
    subject_id_to_name_map = {s['subid']: s['subname'] for s in all_subjects}
    # [START Change 1 - New map for full subject details]
    subject_id_to_full_obj_map = {s['subid']: s for s in all_subjects}
    # [END Change 1 - New map for full subject details]
    
    # Group existing topics by subject ID
    topic_subid_map = {}
    for t in all_topics:
        subid = t['subid']
        tname = t['tname']
        if subid not in topic_subid_map:
            topic_subid_map[subid] = set()
        topic_subid_map[subid].add(tname)

    # --- Create New Topic Section ---
    st.subheader("Create New Topic")
    if not all_subjects:
        st.info("No Subjects available. Please create Subjects first.")
        st.markdown("---")
        return # Exit function if no subjects

    # Select Subject for Creation
    # [START Change 1 - Enhanced Subject Display in Create Section]
    subject_display_options_create = [
        f"{s['subname']} (Level: {s.get('level', 'N/A')}, ID: {s['subid']})" for s in all_subjects
    ]
    # [END Change 1 - Enhanced Subject Display in Create Section]
    selected_subject_create_display = st.selectbox(
        "Select Parent Subject for new Topic",
        options=subject_display_options_create,
        key="create_topic_subject_select"
    )
    # Extract ID using regex for robustness
    selected_subject_create_id = None
    if selected_subject_create_display:
        match = re.search(r"ID: (\d+)", selected_subject_create_display)
        if match:
            selected_subject_create_id = int(match.group(1))

    with st.form("create_topic_form"):
        new_tname = st.text_input("Topic Name", key="new_topic_name_input")
        new_image_url = st.text_input("Image URL (optional)", key="new_topic_image_url_input")

        create_submitted = st.form_submit_button("Create Topic")

        if create_submitted:
            if new_tname and selected_subject_create_id is not None:
                # Check for duplicate topic name within the selected subject
                existing_topics_for_subject = topic_subid_map.get(selected_subject_create_id, set())
                if new_tname in existing_topics_for_subject:
                    st.warning(f"Topic '{new_tname}' already exists for this subject. Please choose a different name.")
                else:
                    with st.spinner("Creating topic..."):
                        result = create_topic(new_tname, selected_subject_create_id, new_image_url)
                        if result:
                            st.success(f"Topic '{result['tname']}' (ID: {result['tid']}) created successfully for Subject ID {result['subid']}!")
                            st.rerun()
                        else:
                            st.error("Failed to create topic. Please check API logs.")
            else:
                st.warning("Please enter Topic Name and select a Parent Subject.")
    
    st.markdown("---") # Separator

    # --- List Existing Topics Section ---
    st.subheader("Existing Topics")
    if all_topics:
        # Enhance with Subject names for better display
        displayed_topics = []
        for t in all_topics:
            # [START Change 1 - Use full subject object for display]
            subject_obj = subject_id_to_full_obj_map.get(t['subid'], {})
            subject_name = subject_obj.get('subname', "N/A Subject")
            subject_level = subject_obj.get('level', 'N/A')
            subject_display_str = f"{subject_name} (Level: {subject_level}, ID: {t['subid']})"
            # [END Change 1 - Use full subject object for display]

            displayed_topics.append({
                "tid": t['tid'],
                "tname": t['tname'],
                "subid": t['subid'],
                "subject_info": subject_display_str, # Changed key to reflect full info
                "image_url": t.get('image_url', '') # Use .get for robustness
            })
        
        # [START Change 1 - Adjust DataFrame columns]
        df_topics = pd.DataFrame(displayed_topics)
        df_topics = df_topics[['tid', 'tname', 'subject_info', 'image_url']] # Adjusted columns
        df_topics.rename(columns={'subject_info': 'Parent Subject'}, inplace=True) # Rename column for better display
        # [END Change 1 - Adjust DataFrame columns]
        st.dataframe(df_topics, use_container_width=True)
    else:
        st.info("No topics found yet.")

    st.markdown("---") # Separator

    # --- Update Existing Topic Section ---
    st.subheader("Update Existing Topic")
    if not all_topics:
        st.info("No topics available to update.")
        st.markdown("---")
        return

    if not all_subjects:
        st.info("No Subjects available for selection in update. Please create Subjects.")
        st.markdown("---")
        return

    # 1. Select Subject for Topic Filtering (for display)
    # [START Change 1 - Enhanced Subject Display in Update Filter Section]
    subject_display_options_filter_update = [
        f"{s['subname']} (Level: {s.get('level', 'N/A')}, ID: {s['subid']})" for s in all_subjects
    ]
    # [END Change 1 - Enhanced Subject Display in Update Filter Section]
    selected_subject_filter_update_display = st.selectbox(
        "Filter Topics by Parent Subject (for selection below)",
        options=subject_display_options_filter_update,
        key="update_topic_subject_filter_select"
    )
    selected_subject_filter_update_id = None
    if selected_subject_filter_update_display:
        match = re.search(r"ID: (\d+)", selected_subject_filter_update_display)
        if match:
            selected_subject_filter_update_id = int(match.group(1))

    # Filter topics based on selected Subject for the topic selection dropdown
    filtered_topics_for_update_selection = [
        t for t in all_topics if t['subid'] == selected_subject_filter_update_id
    ]
    
    if not filtered_topics_for_update_selection:
        st.info(f"No topics found for the selected Subject '{selected_subject_filter_update_display}'.")
        st.markdown("---")
        return

    # 2. Select Topic to Update (filtered by Subject)
    sorted_topics_for_update = sorted(filtered_topics_for_update_selection, key=lambda x: x['tid'])
    topic_options_update = {
        f"ID: {t['tid']} ({t['tname']})": t['tid'] 
        for t in sorted_topics_for_update
    }
    selected_topic_display = st.selectbox(
        "Select Specific Topic to Update",
        options=list(topic_options_update.keys()),
        key="select_specific_topic_to_update"
    )
    selected_topic_id = topic_options_update.get(selected_topic_display)

    current_topic_obj = None
    if selected_topic_id is not None:
        current_topic_obj = next((t for t in all_topics if t['tid'] == selected_topic_id), None)

    if current_topic_obj:
        with st.form("update_topic_form"):
            initial_tname = current_topic_obj['tname']
            initial_subid = current_topic_obj['subid'] # This is the current topic's actual subject ID
            initial_image_url = current_topic_obj.get('image_url', '')

            # [START Change 2 - Display Current Parent Subject and allow changing it]
            current_subject_obj = subject_id_to_full_obj_map.get(initial_subid, {})
            current_subject_display_info = f"{current_subject_obj.get('subname', 'N/A')} (Level: {current_subject_obj.get('level', 'N/A')}, ID: {initial_subid})"
            st.info(f"Current Parent Subject: **{current_subject_display_info}**")

            # Options for changing parent subject: "Keep Current" + all other subjects
            change_subject_options = ["-- Keep Current Subject --"]
            other_subjects = [s for s in all_subjects if s['subid'] != initial_subid]
            # [START Change 1 - Enhanced Subject Display in New Selectbox]
            change_subject_options.extend([
                f"{s['subname']} (Level: {s.get('level', 'N/A')}, ID: {s['subid']})" for s in other_subjects
            ])
            # [END Change 1 - Enhanced Subject Display in New Selectbox]
            
            selected_new_subject_display = st.selectbox(
                "Change Parent Subject (Optional)",
                options=change_subject_options,
                key="change_topic_parent_subject_select"
            )

            new_subid_for_update = initial_subid # Default to current subject ID
            if selected_new_subject_display != "-- Keep Current Subject --":
                match = re.search(r"ID: (\d+)", selected_new_subject_display)
                if match:
                    new_subid_for_update = int(match.group(1))
            # [END Change 2 - Display Current Parent Subject and allow changing it]
            
            updated_tname = st.text_input("New Topic Name", value=initial_tname, key="updated_topic_name_input")
            updated_image_url = st.text_input("New Image URL (optional)", value=initial_image_url, key="updated_topic_image_url_input")
            
            update_submitted = st.form_submit_button("Update Topic")

            if update_submitted:
                if selected_topic_id is not None and updated_tname and new_subid_for_update is not None:
                    # Check for duplicate topic name within the *new* selected subject
                    # If subject is changed, check against topics in the new subject
                    # If subject is not changed, check against topics in the current subject (excluding itself)
                    target_subid_for_duplicate_check = new_subid_for_update
                    
                    existing_topics_in_target_subject = {
                        t['tname'] for t in all_topics 
                        if t['subid'] == target_subid_for_duplicate_check and t['tid'] != selected_topic_id
                    }

                    # If the topic name is changed OR the subject is changed, perform duplicate check
                    if (updated_tname != initial_tname or new_subid_for_update != initial_subid) and \
                       (updated_tname in existing_topics_in_target_subject):
                        st.warning(f"Topic '{updated_tname}' already exists in the selected subject. Please choose a different name or subject.")
                    else:
                        with st.spinner(f"Updating topic ID {selected_topic_id}..."):
                            update_payload = {}
                            if updated_tname != initial_tname:
                                update_payload['tname'] = updated_tname
                            
                            # [START Change 2 - Add new_subid_for_update to payload if changed]
                            if new_subid_for_update != initial_subid:
                                update_payload['subid'] = new_subid_for_update
                            # [END Change 2 - Add new_subid_for_update to payload if changed]
                            
                            if updated_image_url != initial_image_url:
                                update_payload['image_url'] = updated_image_url
                            
                            # --- Debugging Information (Update Section) ---
                            st.info(f"DEBUG (Update): Selected Topic ID: {selected_topic_id}")
                            st.info(f"DEBUG (Update): Initial Data: Name='{initial_tname}', Subject ID='{initial_subid}', Image='{initial_image_url}'")
                            st.info(f"DEBUG (Update): Updated Data: Name='{updated_tname}', New Subject ID='{new_subid_for_update}', Image='{updated_image_url}'")
                            st.info(f"DEBUG (Update): Payload to send: {update_payload}")
                            # --- End Debugging Information ---

                            if not update_payload:
                                st.info("No changes detected. Topic not updated.")
                                st.rerun()
                                return

                            # Pass subid explicitly from new_subid_for_update, if it was changed or not
                            # This ensures it's always included in the payload for validation and consistency
                            # The update_topic function takes subid as an optional parameter,
                            # so explicitly setting it here ensures it's part of the API request.
                            if 'subid' not in update_payload: # Ensure subid is always in payload if not explicitly changed
                                update_payload['subid'] = initial_subid
                                
                            result = update_topic(selected_topic_id, **update_payload)
                            if result:
                                st.success(f"Topic ID {result['tid']} updated successfully!")
                                st.rerun()
                            else:
                                st.error("Failed to update topic. Please check API logs.")
                else:
                    st.warning("Please select a topic and enter a valid name.")
            else:
                st.info("Select a topic from the dropdown to see its details for update.")

    st.markdown("---") # Separator

    # --- Delete Topic Section ---
    st.subheader("Delete Topic")
    if all_topics:
        topic_options_delete = {f"ID: {t['tid']} ({t['tname']})": t['tid'] for t in sorted(all_topics, key=lambda x: x['tid'])}
        selected_topic_display_delete = st.selectbox(
            "Select Topic to Delete",
            options=list(topic_options_delete.keys()),
            key="delete_topic_select"
        )
        selected_topic_id_delete = topic_options_delete.get(selected_topic_display_delete)

        if st.button("Delete Topic", key="delete_topic_button"):
            if selected_topic_id_delete is not None:
                st.session_state.confirm_delete_topic_id = selected_topic_id_delete
                st.warning(f"Are you sure you want to delete Topic ID: {selected_topic_id_delete}? This action cannot be undone.")
            else:
                st.warning("Please select a topic to delete.")
        
        if 'confirm_delete_topic_id' in st.session_state and st.session_state.confirm_delete_topic_id == selected_topic_id_delete:
            if st.button("Confirm Deletion", key="confirm_delete_topic_final_button"):
                with st.spinner(f"Deleting topic ID {selected_topic_id_delete}..."):
                    success = delete_topic(selected_topic_id_delete)
                    if success:
                        st.success(f"Topic ID {selected_topic_id_delete} deleted successfully!")
                        del st.session_state.confirm_delete_topic_id
                        st.rerun()
                    else:
                        st.error("Failed to delete topic. Please check API logs.")
    else:
        st.info("No topics available to delete.")