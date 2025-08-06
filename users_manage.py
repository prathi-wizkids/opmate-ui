# users_manage.py (General User Management)
import streamlit as st
import requests
import pandas as pd

# --- Configuration ---
API_BASE_URL = "http://localhost:5002" # Your Node.js API URL

# --- API Interaction Functions for Users ---

def get_all_users_general():
    """Fetches all users from the backend API (public.users table)."""
    try:
        response = requests.get(f"{API_BASE_URL}/users")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching all users: {e}")
        return []

def create_user_general(username, email, password, role):
    """Creates a new general user entry (and related role entry in backend)."""
    payload = {
        "username": username, # Corrected: Mapped to public.users.username
        "email": email,
        "password": password, # Backend handles hashing and storage in teachers/students table
        "role": role,
    }
    
    # --- Debugging API Request ---
    st.info(f"DEBUG (Create User): Sending payload: {payload}")
    # --- End Debugging API Request ---

    try:
        response = requests.post(f"{API_BASE_URL}/users", json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        # --- Debugging API Response on Error ---
        st.error(f"Error creating user: {e}")
        if e.response is not None:
            st.error(f"API Response Status Code: {e.response.status_code}")
            st.error(f"API Response Text: {e.response.text}")
        # --- End Debugging API Response on Error ---
        return None

def update_user_general(userid, username=None, email=None, password=None, role=None, isdeleted=None):
    """Updates an existing general user entry."""
    payload = {}
    if username is not None:
        payload["username"] = username # Corrected: Mapped to public.users.username
    if email is not None:
        payload["email"] = email
    if password is not None and password: # Only update password if provided and not empty
        payload["password"] = password
    if role is not None:
        payload["role"] = role
    if isdeleted is not None:
        payload["isdeleted"] = isdeleted
    
    # --- Debugging API Request ---
    st.info(f"DEBUG (Update User): Sending payload: {payload}")
    # --- End Debugging API Request ---

    try:
        response = requests.put(f"{API_BASE_URL}/users/{userid}", json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        # --- Debugging API Response on Error ---
        st.error(f"Error updating user: {e}")
        if e.response is not None:
            st.error(f"API Response Status Code: {e.response.status_code}")
            st.error(f"API Response Text: {e.response.text}")
        # --- End Debugging API Response on Error ---
        return None

def delete_user_general(userid):
    """Soft deletes a user from public.users."""
    try:
        # Note: Your API's deleteUser marks isdeleted=true.
        response = requests.delete(f"{API_BASE_URL}/users/{userid}")
        response.raise_for_status()
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        st.error(f"Error soft-deleting user: {e}")
        if e.response is not None:
            st.error(f"API Response Status Code: {e.response.status_code}")
            st.error(f"API Response Text: {e.response.text}")
        return False

# --- Streamlit UI for General User Management ---

def users_manage_page():
    """Renders the UI for managing General Users (from public.users table)."""
    st.header("Manage All Users")
    st.write("Here you can create, view, update, and soft-delete general user accounts.")

    all_users = get_all_users_general()

    # --- Create New User Section ---
    st.subheader("Create New User Account")
    with st.form("create_user_general_form"):
        new_username = st.text_input("User Name", key="new_general_username_input")
        new_email = st.text_input("Email", key="new_general_email_input")
        new_password = st.text_input("Password", type="password", key="new_general_password_input")
        new_role = st.selectbox("Role", options=["student", "teacher"], key="new_general_role_select")

        create_submitted = st.form_submit_button("Create User Account")

        if create_submitted:
            if new_username and new_email and new_password and new_role:
                with st.spinner("Creating user account..."):
                    result = create_user_general(new_username, new_email, new_password, new_role)
                    if result:
                        st.success(f"User '{result['username']}' (ID: {result['userid']}) created successfully as a {result['role']}!")
                        st.rerun()
                    else:
                        st.error("Failed to create user account. This might be a duplicate email or a backend validation error. Please check API logs for more details.")
            else:
                st.warning("Please enter User Name, Email, Password, and select a Role.")
    
    st.markdown("---") # Separator

    # --- List Existing Users Section ---
    st.subheader("Existing User Accounts")
    if all_users:
        df_users = pd.DataFrame(all_users)
        # Display relevant columns
        display_cols = ['userid', 'username', 'email', 'role', 'isdeleted', 'created_at', 'user_role_link']
        st.dataframe(df_users[display_cols], use_container_width=True)
    else:
        st.info("No user accounts found yet.")

    st.markdown("---") # Separator

    # --- Update Existing User Section ---
    st.subheader("Update Existing User Account")
    if all_users:
        sorted_users = sorted(all_users, key=lambda x: x['userid'])
        user_options = {
            f"ID: {u['userid']} ({u['username']} - {u['role']})": u['userid'] 
            for u in sorted_users
        }
        selected_user_display = st.selectbox(
            "Select User Account to Update",
            options=list(user_options.keys()),
            key="update_general_user_select"
        )
        selected_user_id = user_options.get(selected_user_display)

        current_user_obj = None
        if selected_user_id is not None:
            current_user_obj = next((u for u in all_users if u['userid'] == selected_user_id), None)

        if current_user_obj:
            with st.form("update_user_general_form"):
                initial_username = current_user_obj['username']
                initial_email = current_user_obj['email']
                initial_role = current_user_obj['role']
                initial_isdeleted = current_user_obj['isdeleted']

                updated_username = st.text_input("New User Name", value=initial_username, key="updated_general_username_input")
                updated_email = st.text_input("New Email", value=initial_email, key="updated_general_email_input")
                updated_password = st.text_input("New Password (leave empty to keep current)", type="password", key="updated_general_password_input")
                updated_role = st.selectbox("New Role", options=["student", "teacher"], index=["student", "teacher"].index(initial_role), key="updated_general_role_select")
                updated_isdeleted = st.checkbox("Mark as Deleted", value=initial_isdeleted, key="updated_general_isdeleted_checkbox")

                update_submitted = st.form_submit_button("Update User Account")

                if update_submitted:
                    if selected_user_id is not None and updated_username and updated_email and updated_role:
                        with st.spinner(f"Updating user account ID {selected_user_id}..."):
                            update_payload = {}
                            if updated_username != initial_username:
                                update_payload['username'] = updated_username # Corrected: Mapped to public.users.username
                            if updated_email != initial_email:
                                update_payload['email'] = updated_email
                            if updated_password:
                                update_payload['password'] = updated_password
                            if updated_role != initial_role:
                                update_payload['role'] = updated_role
                            if updated_isdeleted != initial_isdeleted:
                                update_payload['isdeleted'] = updated_isdeleted
                            
                            # --- Debugging Information (Update Section) ---
                            st.info(f"DEBUG (Update): Selected User ID: {selected_user_id}")
                            st.info(f"DEBUG (Update): Initial Data: Name='{initial_username}', Email='{initial_email}', Role='{initial_role}', Deleted='{initial_isdeleted}'")
                            st.info(f"DEBUG (Update): Updated Data: Name='{updated_username}', Email='{updated_email}', Role='{updated_role}', Deleted='{updated_isdeleted}', Password provided: {'Yes' if updated_password else 'No'}")
                            st.info(f"DEBUG (Update): Payload to send: {update_payload}")
                            # --- End Debugging Information ---

                            if not update_payload:
                                st.info("No changes detected. User account not updated.")
                                st.rerun()
                                return

                            result = update_user_general(selected_user_id, **update_payload)
                            if result:
                                st.success(f"User account ID {result['userid']} updated successfully!")
                                st.rerun()
                            else:
                                st.error("Failed to update user account. Please check API logs for details (e.g., duplicate email, validation errors).")
                    else:
                        st.warning("Please select a user, enter valid Name, Email, and Role.")
        else:
            st.info("Select a user account from the dropdown to see their details for update.")
    else:
        st.info("No user accounts available to update.")

    st.markdown("---") # Separator

    # --- Delete User Section (Soft Delete) ---
    st.subheader("Soft-Delete User Account")
    if all_users:
        # Only show active users for soft-deletion (isdeleted=false)
        active_users_for_delete = [u for u in all_users if not u.get('isdeleted', False)]
        if active_users_for_delete:
            user_options_delete = {f"ID: {u['userid']} ({u['username']} - {u['role']})": u['userid'] for u in sorted(active_users_for_delete, key=lambda x: x['userid'])}
            selected_user_display_delete = st.selectbox(
                "Select User Account to Soft-Delete",
                options=list(user_options_delete.keys()),
                key="delete_user_general_select"
            )
            selected_user_id_delete = user_options_delete.get(selected_user_display_delete)

            if st.button("Soft-Delete User Account", key="delete_user_general_button"):
                if selected_user_id_delete is not None:
                    st.session_state.confirm_delete_user_general_id = selected_user_id_delete
                    st.warning(f"Are you sure you want to soft-delete User Account ID: {selected_user_id_delete}? This will mark the user as deleted and may affect associated teacher/student records.")
                else:
                    st.warning("Please select a user account to soft-delete.")
            
            if 'confirm_delete_user_general_id' in st.session_state and st.session_state.confirm_delete_user_general_id == selected_user_id_delete:
                if st.button("Confirm Soft-Deletion", key="confirm_delete_user_general_final_button"):
                    with st.spinner(f"Soft-deleting user account ID {selected_user_id_delete}..."):
                        success = delete_user_general(selected_user_id_delete)
                        if success:
                            st.success(f"User account ID {selected_user_id_delete} soft-deleted successfully!")
                            del st.session_state.confirm_delete_user_general_id
                            st.rerun()
                        else:
                            st.error("Failed to soft-delete user account. Please check API logs.")
        else:
            st.info("No active user accounts available for soft-deletion.")
    else:
        st.info("No user accounts found yet to delete.")

