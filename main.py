# main.py
import streamlit as st

# Import all necessary management modules and their functions
# Ensure these imports match your actual file names and function names
from gurukul_manage import gurukul_manage_page
from offerings_manage import offerings_manage_page
from milestones_manage import milestones_manage_page
from subjects_manage import subjects_manage_page
from topics_manage import topics_manage_page
from users_manage import users_manage_page
from u_teachers_manage import u_teachers_manage_page
from u_students_manage import u_students_manage_page
from showTopicbySubject import show_topics_by_subject_page
from showTopicsbyLevel import show_topics_by_level_page

# Imports for the new direct management sections
from DirectTeacher_manage import show_teacher_crud_direct
from DirectStudent_manage import show_student_crud_direct

# --- Helper Function for Navigation ---
def set_view(view_name):
    """Sets the current view in session state and clears cache."""
    st.session_state.current_view = view_name
    st.cache_data.clear() # Clear cache when changing views to ensure fresh data

# --- Main Application ---
def main():
    st.set_page_config(layout="wide", page_title="Gurukul Admin UI")

    # Initialize session state for page navigation, using 'current_view' consistently
    if 'current_view' not in st.session_state:
        st.session_state.current_view = "admin_dashboard" # Default home view

    # --- Sidebar Navigation ---
    with st.sidebar:
        st.title("Admin UI Navigation")
        st.markdown("---")

        # Buttons for different management sections, all using set_view
        if st.button("Manage Gurukuls"):
            set_view("gurukuls_page") # Using a consistent view name
        if st.button("Manage Gurukul Offerings"):
            set_view("offerings_page")
        if st.button("Manage Milestones"):
            set_view("milestones_page")
        if st.button("Manage Subjects"):
            set_view("subjects_page")
        
        st.markdown("---") # Separator for Topics section
        st.markdown("### Topics") # Sub-heading for topics
        if st.button("Manage All Topics"):
            set_view("topics_page")
        if st.button("Show Topics by Subject"):
            set_view("topics_by_subject_page")
        if st.button("Show Topics by Level"):
            set_view("topics_by_level_page")
        
        st.sidebar.markdown("---")
        st.sidebar.subheader("Direct Management (Old Way)")
        # These buttons correctly set 'current_view' for the new direct management pages
        st.sidebar.button("Manage Teachers (Direct)", on_click=lambda: set_view('direct_teacher_crud'))
        st.sidebar.button("Manage Students (Direct)", on_click=lambda: set_view('direct_student_crud'))

        st.markdown("---") # Separator for Users section
        st.markdown("### Users (via public.users)") # Sub-heading for users
        if st.button("Manage All Users"):
            set_view("users_page")
        if st.button("Manage Teachers"):
            set_view("u_teachers_page")
        if st.button("Manage Students"):
            set_view("u_students_page")

        # Optional: A "Back to Dashboard" button for all sub-pages
        st.markdown("---")
        if st.session_state.current_view != "admin_dashboard":
            st.button("↩️ Back to Dashboard", on_click=lambda: set_view('admin_dashboard'))


    # --- Main Content Area ---
    st.markdown("---") # Add a horizontal line for visual separation

    # All content rendering now checks 'st.session_state.current_view'
    if st.session_state.current_view == "admin_dashboard":
        st.header("Welcome to Admin UI!")
        st.info("Select a management section from the sidebar to get started.")
        # Assuming "flower.png" exists in your project directory
        st.image("flower.png", caption="", use_container_width=True)

    # Existing Management Pages
    elif st.session_state.current_view == "gurukuls_page":
        gurukul_manage_page()
    elif st.session_state.current_view == "offerings_page":
        offerings_manage_page()
    elif st.session_state.current_view == "milestones_page":
        milestones_manage_page()
    elif st.session_state.current_view == "subjects_page":
        subjects_manage_page()
    elif st.session_state.current_view == "topics_page":
        topics_manage_page()
    elif st.session_state.current_view == "users_page":
        users_manage_page()
    elif st.session_state.current_view == "u_teachers_page":
        u_teachers_manage_page()
    elif st.session_state.current_view == "u_students_page":
        u_students_manage_page()
    elif st.session_state.current_view == "topics_by_subject_page":
        show_topics_by_subject_page()
    elif st.session_state.current_view == "topics_by_level_page":
        show_topics_by_level_page()
    
    # Direct Management (Old Way) Pages - These will now correctly open
    elif st.session_state.current_view == 'direct_teacher_crud':
        show_teacher_crud_direct()
    elif st.session_state.current_view == 'direct_student_crud':
        show_student_crud_direct()


if __name__ == "__main__":
    main()
