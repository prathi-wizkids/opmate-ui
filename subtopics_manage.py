# subtopics_manage.py
import streamlit as st
import requests
import json
import re # Import regex for parsing IDs from display strings

# --- Configuration ---
#API_BASE_URL = "http://localhost:5002" # Your Node.js API URL
from config import API_BASE_URL

# --- API Interaction Functions (re-used or adapted for this module) ---

def direct_api_call(method, endpoint, payload=None):
    """
    Handles direct API calls to the backend.
    Includes robust error handling and debug logging.
    """
    url = f"{API_BASE_URL}{endpoint}" # endpoint should now directly be /subtopics or /subtopics/by-topic/X
    headers = {"Content-Type": "application/json"}
    
    try:
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

        if response.status_code == 204: # No Content
            print(f"DEBUG API RESPONSE: Status=204 (No Content) for {endpoint}")
            return response.status_code, {}

        try:
            data = response.json()
            print(f"DEBUG API RESPONSE: Status={response.status_code}, Data={data} for {endpoint}")
        except json.JSONDecodeError:
            print(f"DEBUG: JSONDecodeError for {method} {url}. Raw response content: '{response.text}'")
            return response.status_code, {"message": f"Invalid JSON response from API: {response.text}"}

        return response.status_code, data

    except requests.exceptions.ConnectionError:
        st.error(f"Failed to connect to API at {API_BASE_URL}. Please ensure the backend server is running.")
        print(f"ERROR: ConnectionError to API at {API_BASE_URL}")
        return 503, {"message": "API service unavailable"}
    except requests.exceptions.Timeout:
        st.error("API request timed out.")
        print("ERROR: API request timed out.")
        return 408, {"message": "API request timed out"}
    except requests.exceptions.RequestException as e:
        st.error(f"An unexpected error occurred during API request: {e}")
        print(f"ERROR: Unexpected API request error: {e}")
        return 500, {"message": f"API request error: {e}"}


@st.cache_data(ttl=60)
def fetch_all_topics_for_subtopic_management():
    """Fetches all topics (tid, tname, subid, image_url) for use in dropdowns."""
    status, data = direct_api_call('GET', '/topics')
    if status == 200:
        return data
    st.error(f"Failed to fetch topics: {data.get('message', 'Unknown error')}")
    return []

@st.cache_data(ttl=60)
def fetch_all_subtopics_for_filtering():
    """NEW: Fetches all subtopics to determine which topics have subtopics."""
    status, data = direct_api_call('GET', '/subtopics') # CORRECTED: Removed /api
    if status == 200:
        return data
    st.error(f"Failed to fetch all subtopics for filtering: {data.get('message', 'Unknown error')}")
    return []

@st.cache_data(ttl=60)
def fetch_subtopics_by_topic(topic_id):
    """Fetches subtopics for a given topic ID."""
    if topic_id is None:
        return []
    status, data = direct_api_call('GET', f'/subtopics/by-topic/{topic_id}') # CORRECTED: Removed /api
    if status == 200:
        return data
    st.error(f"Failed to fetch subtopics for Topic ID {topic_id}: {data.get('message', 'Unknown error')}")
    return []

def create_subtopic_api(topic_id, subtopic_name, image_url):
    """Calls the API to create a new subtopic."""
    payload = {
        "topicId": topic_id,
        "subtopicName": subtopic_name,
        "imageUrl": image_url
    }
    status, data = direct_api_call('POST', '/subtopics', payload) # CORRECTED: Removed /api
    return status, data

def update_subtopic_api(subtid, payload):
    """Calls the API to update an existing subtopic."""
    status, data = direct_api_call('PUT', f'/subtopics/{subtid}', payload) # CORRECTED: Removed /api
    return status, data

# --- Streamlit UI for Subtopic Management ---

def subtopics_manage_page():
    """Renders the UI for managing Subtopics."""
    st.header("Manage Subtopics")
    st.write("Here you can create, view, and update Subtopics.")

    # Fetch all necessary data
    all_topics = fetch_all_topics_for_subtopic_management()
    all_subtopics = fetch_all_subtopics_for_filtering() # NEW: Fetch all subtopics for filtering

    # Create maps for easy lookup
    topic_id_to_obj_map = {t['tid']: t for t in all_topics}
    
    # Determine which topics have subtopics
    topic_ids_with_subtopics = {subt['topic_id'] for subt in all_subtopics}

    # Prepare topic display options for creation (all topics)
    topic_display_options_all = ["-- Select Topic --"] + sorted([
        f"{t['tname']} (ID: {t['tid']})" for t in all_topics
    ])

    # Prepare topic display options for listing/updating (only topics with subtopics)
    filtered_topics_for_display = [
        t for t in all_topics if t['tid'] in topic_ids_with_subtopics
    ]
    topic_display_options_with_subtopics = ["-- Select Topic --"] + sorted([
        f"{t['tname']} (ID: {t['tid']})" for t in filtered_topics_for_display
    ])


    # --- Create New Subtopic Section ---
    st.subheader("Create New Subtopic")
    if not all_topics:
        st.info("No Topics available. Please create Topics first to add Subtopics.")
        st.markdown("---")
        return # Exit function if no topics

    selected_topic_create_display = st.selectbox(
        "Select Parent Topic for new Subtopic",
        options=topic_display_options_all, # Use all topics for creation
        key="create_subtopic_topic_select"
    )
    selected_topic_create_id = None
    if selected_topic_create_display != "-- Select Topic --":
        match = re.search(r"ID: (\d+)", selected_topic_create_display)
        if match:
            selected_topic_create_id = int(match.group(1))

    with st.form("create_subtopic_form", clear_on_submit=True):
        new_subtopic_name = st.text_input("Subtopic Name", key="new_subtopic_name_input")
        new_subtopic_image_url = st.text_input("Image URL (optional)", key="new_subtopic_image_url_input")

        create_submitted = st.form_submit_button("Create Subtopic")

        if create_submitted:
            if new_subtopic_name and selected_topic_create_id is not None:
                with st.spinner("Creating subtopic..."):
                    status, result = create_subtopic_api(selected_topic_create_id, new_subtopic_name, new_subtopic_image_url)
                    if status == 201:
                        st.success(f"Subtopic '{result['subtopic_name']}' (ID: {result['subtid']}) created successfully for Topic ID {result['topic_id']}!")
                        st.cache_data.clear()
                        st.rerun()
                    elif status == 409:
                        st.warning(f"Failed to create subtopic: {result.get('message', 'Subtopic with this name already exists for this topic.')}")
                    else:
                        st.error(f"Failed to create subtopic: {result.get('message', 'Unknown error')}")
            else:
                st.warning("Please enter Subtopic Name and select a Parent Topic.")
    
    st.markdown("---") # Separator

    # --- List Existing Subtopics Section ---
    st.subheader("Existing Subtopics")

    # NEW: Use the filtered list for the dropdown
    if not filtered_topics_for_display:
        st.info("No Topics with Subtopics found. Create some above!")
        st.markdown("---")
        return

    selected_topic_list_display = st.selectbox(
        "Select Topic to view its Subtopics",
        options=topic_display_options_with_subtopics, # Use filtered list here
        key="list_subtopic_topic_select"
    )
    selected_topic_list_id = None
    if selected_topic_list_display != "-- Select Topic --":
        match = re.search(r"ID: (\d+)", selected_topic_list_display)
        if match:
            selected_topic_list_id = int(match.group(1))

    if selected_topic_list_id is not None:
        subtopics = fetch_subtopics_by_topic(selected_topic_list_id)
        if subtopics:
            displayed_subtopics = []
            for subt in subtopics:
                displayed_subtopics.append({
                    "Subtopic ID": subt['subtid'],
                    "Subtopic Name": subt['subtopic_name'],
                    "Parent Topic ID": subt['topic_id'],
                    "Image URL": subt.get('image_url', '')
                })
            st.dataframe(displayed_subtopics, use_container_width=True)
        else:
            # This case should ideally not be hit if the dropdown is filtered correctly,
            # but it's good for robustness if a topic somehow loses all its subtopics.
            st.info(f"No subtopics found for Topic '{selected_topic_list_display}'.")
    else:
        st.info("Please select a Topic to view its subtopics.")

    st.markdown("---") # Separator

    # --- Update Existing Subtopic Section ---
    st.subheader("Update Existing Subtopic")

    # NEW: Use the filtered list for the dropdown
    if not filtered_topics_for_display:
        st.info("No Topics with Subtopics found to update. Create some above!")
        st.markdown("---")
        return

    # First, select the parent topic to filter subtopics
    selected_topic_update_filter_display = st.selectbox(
        "Select Parent Topic to filter Subtopics for Update",
        options=topic_display_options_with_subtopics, # Use filtered list here
        key="update_subtopic_topic_filter_select"
    )
    selected_topic_update_filter_id = None
    if selected_topic_update_filter_display != "-- Select Topic --":
        match = re.search(r"ID: (\d+)", selected_topic_update_filter_display)
        if match:
            selected_topic_update_filter_id = int(match.group(1))

    subtopics_for_update_selection = []
    if selected_topic_update_filter_id is not None:
        subtopics_for_update_selection = fetch_subtopics_by_topic(selected_topic_update_filter_id)

    if not subtopics_for_update_selection:
        st.info(f"No subtopics found for Topic '{selected_topic_update_filter_display}' to update.")
        st.markdown("---")
        return

    # Then, select the specific subtopic to update
    sorted_subtopics_for_update = sorted(subtopics_for_update_selection, key=lambda x: x['subtid'])
    subtopic_options_update = {
        f"ID: {subt['subtid']} ({subt['subtopic_name']})": subt['subtid'] 
        for subt in sorted_subtopics_for_update
    }
    
    # Check if subtopic_options_update is empty before trying to access keys
    if not subtopic_options_update:
        st.info("No subtopics available for the selected topic.")
        return

    selected_subtopic_display = st.selectbox(
        "Select Specific Subtopic to Update",
        options=list(subtopic_options_update.keys()),
        key="select_specific_subtopic_to_update"
    )
    selected_subtopic_id = subtopic_options_update.get(selected_subtopic_display)

    current_subtopic_obj = None
    if selected_subtopic_id is not None:
        current_subtopic_obj = next((subt for subt in subtopics_for_update_selection if subt['subtid'] == selected_subtopic_id), None)

    if current_subtopic_obj:
        with st.form("update_subtopic_form"):
            # Ensure text inputs are populated with current values for editing
            initial_subtopic_name = current_subtopic_obj['subtopic_name']
            initial_image_url = current_subtopic_obj.get('image_url', '')

            updated_subtopic_name = st.text_input("New Subtopic Name", value=initial_subtopic_name, key="updated_subtopic_name_input")
            updated_image_url = st.text_input("New Image URL (optional)", value=initial_image_url, key="updated_subtopic_image_url_input")
            
            update_submitted = st.form_submit_button("Update Subtopic")

            if update_submitted:
                if selected_subtopic_id is not None and updated_subtopic_name:
                    # Check for duplicate subtopic name within the same parent topic (excluding itself)
                    existing_subtopics_in_topic = {
                        s['subtopic_name'] for s in subtopics_for_update_selection 
                        if s['subtid'] != selected_subtopic_id
                    }

                    if updated_subtopic_name != initial_subtopic_name and \
                       updated_subtopic_name in existing_subtopics_in_topic:
                        st.warning(f"Subtopic '{updated_subtopic_name}' already exists in this topic. Please choose a different name.")
                    else:
                        with st.spinner(f"Updating subtopic ID {selected_subtopic_id}..."):
                            # The API expects a payload with "subtopicName" and "imageUrl" keys
                            update_payload = {}
                            # Only add to payload if the value has changed
                            if updated_subtopic_name != initial_subtopic_name:
                                update_payload['subtopicName'] = updated_subtopic_name
                            if updated_image_url != initial_image_url:
                                update_payload['imageUrl'] = updated_image_url
                            
                            if not update_payload:
                                st.info("No changes detected. Subtopic not updated.")
                                # Use st.experimental_rerun() for older Streamlit versions, st.rerun() for newer
                                st.rerun()
                                return

                            status, result = update_subtopic_api(selected_subtopic_id, update_payload)
                            if status == 200:
                                st.success(f"Subtopic ID {result['subtid']} updated successfully!")
                                st.cache_data.clear()
                                st.rerun()
                            elif status == 409:
                                st.warning(f"Failed to update subtopic: {result.get('message', 'Subtopic with this name already exists for this topic.')}")
                            else:
                                st.error(f"Failed to update subtopic: {result.get('message', 'Unknown error')}")
                else:
                    st.warning("Please select a subtopic and enter a valid name.")
    else:
        st.info("Select a subtopic from the dropdown to see its details for update.")

    st.markdown("---") # Separator
    # Note: No delete section as per user's request.