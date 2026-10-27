import streamlit as st
import pandas as pd
import os
import hashlib
import binascii

def hash_password(password, salt=None):
    """Hashes a password using SHA-256 and a salt."""
    if salt is None:
        salt = os.urandom(16)
    if isinstance(salt, str):
        salt = binascii.unhexlify(salt)
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return binascii.hexlify(salt).decode('utf-8'), binascii.hexlify(pwd_hash).decode('utf-8')

def render(DATA_FOLDER):
    st.subheader("User Account Management")

    users_file = "users.csv" if os.path.exists("users.csv") else os.path.join(DATA_FOLDER, "users.csv")

    if not os.path.exists(users_file):
        st.error(f"Could not find `users.csv` at {users_file}.")
        return

    try:
        users_df = pd.read_csv(users_file)
        users_df.columns = users_df.columns.str.strip()
    except Exception as e:
        st.error(f"Error loading users file: {e}")
        return

    # Dynamically find username and role column names (case-insensitive)
    cols_lower = {col.lower(): col for col in users_df.columns}
    username_col = cols_lower.get("username", cols_lower.get("user", users_df.columns[0]))
    role_col = cols_lower.get("role", cols_lower.get("permission", users_df.columns[-1]))

    # --- Display Existing Users ---
    st.markdown("### Active System Users")
    display_cols = [col for col in users_df.columns if "password" not in col.lower() and "salt" not in col.lower()]
    st.dataframe(users_df[display_cols], use_container_width=True, hide_index=True)

    st.divider()

    col1, col2 = st.columns(2)

    # --- Add New User Form ---
    with col1:
        with st.expander("Add New User", expanded=True):
            with st.form("add_user_form", clear_on_submit=True):
                new_username = st.text_input("Username")
                new_password = st.text_input("Password", type="password")
                new_role = st.selectbox(
                    "Assign Role",
                    ["Administrator", "Safety Officer", "Mining Engineer", "Maintenance Engineer", "Manager"]
                )

                submit_add = st.form_submit_button("Create User")

                if submit_add:
                    if not new_username.strip() or not new_password.strip():
                        st.error("Username and password cannot be empty.")
                    elif new_username.strip() in users_df[username_col].astype(str).values:
                        st.error(f"User '{new_username}' already exists.")
                    else:
                        salt, pwd_hash = hash_password(new_password)
                        
                        # Build row dynamically based on detected columns or standard schema
                        new_row = {
                            username_col: new_username.strip(),
                            "password_hash": pwd_hash,
                            "salt": salt,
                            role_col: new_role
                        }
                        
                        updated_df = pd.concat([users_df, pd.DataFrame([new_row])], ignore_index=True)
                        updated_df.to_csv(users_file, index=False)
                        st.success(f"User '{new_username}' added successfully!")
                        st.rerun()

    # --- Remove User Form ---
    with col2:
        with st.expander("Remove User", expanded=True):
            with st.form("remove_user_form"):
                user_list = users_df[username_col].tolist()
                target_user = st.selectbox("Select User to Remove", user_list)

                submit_remove = st.form_submit_button("Delete User Account", type="primary")

                if submit_remove:
                    current_user = st.session_state.get("username", "")
                    if target_user == current_user:
                        st.error("You cannot delete your own active account while logged in.")
                    elif len(users_df[users_df[role_col].astype(str).str.lower() == "administrator"]) <= 1 and users_df[users_df[username_col] == target_user][role_col].values[0].lower() == "administrator":
                        st.error("Cannot delete the last remaining Administrator account.")
                    else:
                        updated_df = users_df[users_df[username_col] != target_user]
                        updated_df.to_csv(users_file, index=False)
                        st.success(f"User '{target_user}' has been removed.")
                        st.rerun()