# showTopicsbyLevel.py
import streamlit as st
import requests
import pandas as pd
import re # Import the regular expression module

# --- Configuration ---
#API_BASE_URL = "http://localhost:5002" # Your Node.js API URL
from config import API_BASE_URL

# --- API Interaction Functions ---

def get_all_subjects_api():
    """Fetches all subjects from the backend API."""
    try:
        response = requests.get(f"{API_BASE_URL}/subjects")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching subjects: {e}")
        return []

def get_all_topics_api():
    """Fetches all topics from the backend API."""
    try:
        response = requests.get(f"{API_BASE_URL}/topics")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching topics: {e}")
        return []

# --- Streamlit UI ---

def show_topics_by_level_page():
    """Renders the UI for showing topics filtered by level and then subject."""
    st.header("View Topics by Level and Subject")
    st.write("First, select a Level, then a Subject within that Level to view its associated topics.")

    all_subjects = get_all_subjects_api()
    all_topics = get_all_topics_api()

    # Create a map for subject ID to name lookup
    subject_id_to_name_map = {s['subid']: s['subname'] for s in all_subjects}

    if not all_subjects:
        st.info("No subjects found. Please ensure subjects are created in the 'Manage Subjects' section.")
        return

    # --- Select Level ---
    # Get unique levels, excluding None, and sort them
    unique_levels = sorted(list(set([s.get('level') for s in all_subjects if s.get('level') is not None])))
    level_options = ["--- Select a Level ---"] + unique_levels

    selected_level = st.selectbox(
        "Select Level",
        options=level_options,
        key="select_level_for_topics_view_by_level_page" # Changed key for uniqueness
    )

    st.markdown("---")

    # Filter subjects based on selected level
    filtered_subjects_by_level = []
    if selected_level == "--- Select a Level ---":
        filtered_subjects_by_level = all_subjects # Show all subjects if no level is selected
    else:
        filtered_subjects_by_level = [
            s for s in all_subjects if s.get('level') == selected_level
        ]
    
    if not filtered_subjects_by_level and selected_level != "--- Select a Level ---": # Only show info if a specific level chosen but no subjects found
        st.info(f"No subjects found for Level: '{selected_level}'.")
        # No return here, so user can still change level or subject selection
    
    # --- Select Subject (filtered by level) ---
    subject_options = ["--- Select a Subject ---"] + sorted(
        [f"{s['subname']} (Level: {s.get('level', 'N/A')}, ID: {s['subid']})" for s in filtered_subjects_by_level]
    )

    # Use a unique key for this selectbox as well
    selected_subject_display = st.selectbox(
        "Select a Subject",
        options=subject_options,
        key="select_subject_for_topics_by_level_view" # Changed key for uniqueness
    )

    selected_subject_id = None
    if selected_subject_display != "--- Select a Subject ---":
        try:
            # Extract ID from string format: "SubjectName (Level: X, ID: Y)"
            match = re.search(r"ID:\s*(\d+)\)", selected_subject_display)
            if match:
                selected_subject_id = int(match.group(1))
            else:
                st.error("Error parsing subject ID: Cannot find expected 'ID: <number>)' format.")
                selected_subject_id = None
        except ValueError:
            st.error("Error converting subject ID to number. Please select a valid subject.")
            selected_subject_id = None

    st.markdown("---")

    # --- Display Topics ---
    if selected_subject_id is not None:
        st.subheader(f"Topics for: {subject_id_to_name_map.get(selected_subject_id, 'N/A')}")
        
        # Filter topics based on the selected subject ID
        filtered_topics = [
            topic for topic in all_topics if topic.get('subid') == selected_subject_id
        ]

        if filtered_topics:
            display_topics_data = []
            for topic in filtered_topics:
                display_topics_data.append({
                    "Topic ID": topic['tid'],
                    "Topic Name": topic['tname'],
                    "Subject Name": subject_id_to_name_map.get(topic['subid'], 'N/A'),
                    "Image URL": topic.get('image_url', 'N/A')
                })
            df_topics = pd.DataFrame(display_topics_data)
            st.dataframe(df_topics, use_container_width=True)
        else:
            st.info(f"No topics found for '{subject_id_to_name_map.get(selected_subject_id, 'N/A')}'.")
    else:
        st.info("Please select a Level and a Subject from the dropdowns above to view its topics.")

