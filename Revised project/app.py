import streamlit as st
import pandas as pd
import hashlib
import importlib
import base64
import os
from pathlib import Path
from PIL import Image


# Get the folder where app.py is currently living on whoever's computer is running it
BASE_DIR = Path(__file__).resolve().parent
BACKGROUND_IMAGE = BASE_DIR / "views" / "mining_app_background_contrast_changed.jpg"
ICON_IMAGE = BASE_DIR / "views" / "wits_logo.png"

st.set_page_config(
    page_title="KHWEZI MINE",
    page_icon=Image.open(ICON_IMAGE),
    layout="wide"
)

def display_header():
    """Display the School of Mining logo and KHWEZI MINE title."""
    
    # 1. Convert your image to Base64 so it can be injected into HTML
    with open(ICON_IMAGE, "rb") as img_file:
        img_base64 = base64.b64encode(img_file.read()).decode()

    logo_col, title_col = st.columns([1, 8])

    with logo_col:
        # 2. Put the <img> tag INSIDE the styled <div>
        st.markdown(
            f"""
            <div style="
                background-color: white;
                border-radius: 12px;
                padding: 12px;
                display: flex;
                justify-content: center;
                align-items: center;
                width: 130px;
                height: 110px;
                box-sizing: border-box;
                margin-bottom: 10px;
            ">
                <img src="data:image/png;base64,{img_base64}" style="max-width: 100%; max-height: 100%; object-fit: contain;">
            </div>
            """,
            unsafe_allow_html=True
        )

    with title_col:
        st.markdown(
            """
            <div style="padding-top: 10px;">
                <h1 style="
                    color: #FFFFFF;
                    font-size: 32px;
                    margin-bottom: 0;
                ">
                    KHWEZI MINE
                </h1>
                <p style="
                    color: #EAAA18;
                    font-size: 16px;
                    margin-top: 0;
                ">
                    Powered by Wits
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.divider()

with open(BACKGROUND_IMAGE, "rb") as image_file:
    encoded_image = base64.b64encode(image_file.read()).decode()


st.markdown(
    f"""
    <style>
    /* Background image with a dark gradient overlay (scrim) for contrast */
    .stApp {{
        background-image: linear-gradient(rgba(11, 15, 25, 0.45), rgba(11, 15, 25, 0.45)), url("data:image/jpeg;base64,{encoded_image}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    
    /* Main headings */
    .stApp h1, .stApp h2, .stApp h3 {{
        color: #FFFFFF !important;
        font-weight: 600;
    }}
    
    /* General text */
    .stApp p, .stApp label, .stApp li {{
        color: #E5E7EB;
    }}
    
    /* Input fields */
    .stTextInput input {{
        color: #FFFFFF !important;
        background-color: rgba(20, 25, 35, 0.85) !important;
    }}
    
    /* Input placeholders */
    .stTextInput input::placeholder {{
        color: #C0C7D1 !important;
    }}
    
    /* Sidebar background */
    [data-testid="stSidebar"] {{
        background-color: rgba(15, 23, 35, 0.96);
    }}
    
    /* Sidebar text */
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label {{
        color: #F3F4F6 !important;
    }}
    
    /* Metric container cards */
    [data-testid="stMetric"] {{
        background-color: rgba(17, 24, 39, 0.85) !important;
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 16px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }}
    
    /* Metric labels */
    [data-testid="stMetricLabel"] {{
        color: #9CA3AF !important;
    }}
    
    /* Metric values */
    [data-testid="stMetricValue"] {{
        color: #FFFFFF !important;
        font-weight: 700 !important;
    }}

    /* Gold divider */
    hr {{
        border-top: 2px solid #EAAA18 !important;
        opacity: 1 !important;
    }}
    
    /* Buttons */
    .stButton button, .stFormSubmitButton button {{
        background-color: #EAAA18 !important;
        color: #111827 !important;
        font-weight: 600;
        border: none;
        border-radius: 7px;
    }}
    
    /* Button hover effect */
    .stButton button:hover, .stFormSubmitButton button:hover {{
        background-color: #F5BE42 !important;
        color: #111827 !important;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# Automatically point to the 'data' folder inside your project directory
DATA_FOLDER = BASE_DIR / "data"

# Fallback check if the data folder is in the current working directory
if not DATA_FOLDER.exists():
    DATA_FOLDER = Path("data")

# This will now correctly evaluate to whatever path their PC uses!
USERS_FILE = DATA_FOLDER / "users.csv"


# Load user accounts
@st.cache_data
def load_users():
    data = pd.read_csv(USERS_FILE, sep=',', dtype=str).fillna("")
    data.columns = data.columns.str.strip()

    for column in [
        "Username", "Role", "Salt",
        "Password_Hash", "Active"
    ]:
        data[column] = data[column].str.strip()

    return data


# Pages available to each role
permissions = {
    "Administrator": [
        "Dashboard", "Worker Safety", "Safety Incidents",
        "Equipment","Risk Assessment",
        "Reports", "Manage Users"
    ],
    "Safety Officer": [
        "Dashboard", "Worker Safety", "Safety Incidents",
        "Risk Assessment", "Reports"
    ],
    "Mining Engineer": [
        "Dashboard", "Worker Safety", "Safety Incidents",
        "Equipment", "Risk Assessment",
        "Reports"
    ],
    "Maintenance Engineer": [
        "Dashboard", "Equipment", "Reports"
    ],
    "Manager": [
        "Dashboard", "Worker Safety", "Safety Incidents",
        "Equipment", "Risk Assessment",
        "Reports"
    ]
}


# Keep track of the login session
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = ""

if "role" not in st.session_state:
    st.session_state.role = ""


# Display the login page
if not st.session_state.logged_in:
    display_header()
    st.subheader("User Login")

    with st.form("login_form"):
        username = st.text_input("Username").strip()
        password = st.text_input(
            "Password",
            type="password"
        )
        submitted = st.form_submit_button("Login")

    if submitted:
        try:
            users_data = load_users()

            required_columns = [
                "Username", "Role", "Salt",
                "Password_Hash", "Active"
            ]

            if not all(
                column in users_data.columns
                for column in required_columns
            ):
                st.error("The users.csv file is missing required columns.")

            else:
                matching_users = users_data[
                    users_data["Username"] == username
                ]

                if matching_users.empty:
                    st.error("Username not found.")

                else:
                    user = matching_users.iloc[0]

                    if user["Active"].lower() != "yes":
                        st.error("This account is inactive.")

                    else:
                        entered_hash = hashlib.sha256(
                            (
                                user["Salt"] + password
                            ).encode("utf-8")
                        ).hexdigest()

                        if entered_hash == user["Password_Hash"]:
                            st.session_state.logged_in = True
                            st.session_state.username = username
                            st.session_state.role = user["Role"]
                            st.rerun()

                        else:
                            st.error("Incorrect password.")

        except FileNotFoundError:
            st.error(
                "Could not find users.csv. Check the dataset folder path."
            )

        except Exception as error:
            st.error(f"Could not load user accounts: {error}")


# Display the application after successful login
else:
    username = st.session_state.username
    role = st.session_state.role
    display_header()
    st.sidebar.title("Navigation")
    st.sidebar.write(f"**User:** {username}")
    st.sidebar.write(f"**Role:** {role}")

    allowed_pages = permissions.get(role, [])

    if not allowed_pages:
        st.error("No pages are configured for this user's role.")

    else:
        page = st.sidebar.radio(
            "Select a page",
            allowed_pages
        )

        st.success(f"Welcome, {username}!")

        if page == "Dashboard":
            st.subheader("Dashboard")

            try:
                workers = pd.read_csv(
                    os.path.join(DATA_FOLDER, "workers.csv")
                )
                incidents = pd.read_csv(
                    os.path.join(DATA_FOLDER, "incidents.csv")
                )
                equipment = pd.read_csv(
                    os.path.join(DATA_FOLDER, "equipment.csv")
                )
                maintenance = pd.read_csv(
                    os.path.join(DATA_FOLDER, "maintenance.csv")
                )

                # Clean column names
                for df in [workers, incidents, equipment, maintenance]:
                    df.columns = df.columns.str.strip()

                # Worker safety
                total_workers = len(workers)
                ppe_scores = pd.to_numeric(
                    workers["PPE_Compliance_Pct"],
                    errors="coerce"
                )
                average_ppe = ppe_scores.mean()

                # Safety incidents
                total_incidents = len(incidents)
                open_incidents = incidents[
                    incidents["Incident_Status"]
                    .astype(str).str.strip().str.lower()
                    .isin(["open", "under investigation"])
                ].shape[0]

                # Equipment
                total_equipment = len(equipment)
                critical_equipment = equipment[
                    equipment["Critical_Alert_Count_30d"] > 0
                ].shape[0]

                average_availability = pd.to_numeric(
                    equipment["Availability_Pct"],
                    errors="coerce"
                ).mean()

                # Maintenance
                overdue_equipment = equipment[
                    equipment["Maintenance_Status"]
                    .astype(str).str.strip().str.lower() == "overdue"
                ].shape[0]

                overdue_work_orders = maintenance[
                    maintenance["Status"]
                    .astype(str).str.strip().str.lower() == "overdue"
                ].shape[0]

                # Dashboard metrics
                st.markdown("### Worker Safety and Incidents")
                col1, col2, col3 = st.columns(3)

                col1.metric("Total Workers", total_workers)
                col2.metric(
                    "Average PPE Compliance",
                    f"{average_ppe:.1f}%"
                    if pd.notna(average_ppe) else "N/A"
                )
                col3.metric("Total Incidents", total_incidents)

                col1, col2 = st.columns(2)
                col1.metric("Open / Investigating Incidents", open_incidents)
                col2.metric(
                    "Workers with High/Critical Risk",
                    workers["Risk_Level"].astype(str).str.strip()
                    .str.lower().isin(["high", "critical"]).sum()
                )

                st.divider()
                st.markdown("### Equipment and Maintenance")

                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Total Equipment", total_equipment)
                col2.metric(
                    "Equipment with Critical Alerts",
                    critical_equipment
                )
                col3.metric(
                    "Average Availability",
                    f"{average_availability:.1f}%"
                    if pd.notna(average_availability) else "N/A"
                )
                col4.metric("Overdue Equipment", overdue_equipment)

                st.metric(
                    "Overdue Maintenance Work Orders",
                    overdue_work_orders
                )

                st.divider()
                st.markdown("### Alerts and Notifications")

                # Import the alert-generation function
                from views.risk_assessment import generate_alerts

                # Load datasets
                eq_df = pd.read_csv(os.path.join(DATA_FOLDER, "equipment.csv"))
                wk_df = pd.read_csv(os.path.join(DATA_FOLDER, "workers.csv"))
                inc_df = pd.read_csv(os.path.join(DATA_FOLDER, "incidents.csv"))

                # Map column names to those expected by the alerts engine
                eq_df = eq_df.rename(columns={
                    "Equipment_ID": "equipment_id",
                    "Temperature_C": "temperature",
                    "Vibration_mm_s": "vibration",
                    "Availability_Pct": "availability",
                    "Downtime_90d_h": "downtime",
                    "Maintenance_Status": "maintenance_status"
                })

                wk_df = wk_df.rename(columns={
                    "Worker_ID": "worker_id",
                    "PPE_Compliance_Pct": "ppe_compliance",
                    "Fatigue_Level": "fatigue_level"
                })

                inc_df = inc_df.rename(columns={
                    "Incident_ID": "incident_id",
                    "Severity": "severity"
                })

                # Prepare data for the alerts engine
                report_data = {
                    "equipment": eq_df,
                    "workers": wk_df,
                    "incidents": inc_df
                }

                # Include risk assessments if the file exists
                risk_file_path = os.path.join(DATA_FOLDER, "risk_assessments.csv")

                if os.path.exists(risk_file_path):
                    risks_df = pd.read_csv(risk_file_path)
                    risks_df.columns = risks_df.columns.str.strip()
                    report_data["risks"] = risks_df

                # Generate alerts without displaying the full alerts page
                alerts_df = generate_alerts(report_data)

                # Count critical alerts and warnings
                if alerts_df.empty:
                    crit_count = 0
                    warn_count = 0
                else:
                    crit_count = int(
                        (alerts_df["Level"] == "CRITICAL").sum()
                    )
                    warn_count = int(
                        (alerts_df["Level"] == "WARNING").sum()
                    )

                # Display ONLY the two KPI cards
                col1, col2 = st.columns(2)

                col1.metric("Critical Alerts", crit_count)
                col2.metric("Warnings", warn_count)

                st.success("Dashboard data loaded successfully.")

            except FileNotFoundError as error:
                st.error(f"Dataset file not found: {error.filename}")

            except KeyError as error:
                st.error(
                    f"Column not found: {error}. "
                    "Please check the dataset column names."
                )
       
        elif page == "Worker Safety":
            st.subheader("Worker Health and Safety")
            try:
                workers = pd.read_csv(os.path.join(DATA_FOLDER, "workers.csv"))

                workers.columns = workers.columns.str.strip()

                # Display key safety indicators
                st.markdown("### Safety Overview")

                total_workers = len(workers)

                average_ppe = pd.to_numeric(
                    workers["PPE_Compliance_Pct"],
                    errors="coerce"
                ).mean()

                high_risk = workers["Risk_Level"].astype(
                    str
                ).str.strip().str.lower().isin(
                    ["high", "critical"]
                ).sum()

                non_compliant = (
                    workers["PPE_Compliant"].astype(str)
                    .str.strip().str.lower() == "no"
                ).sum()

                col1, col2, col3, col4 = st.columns(4)

                col1.metric("Total Workers", total_workers)

                col2.metric(
                    "Average PPE Compliance",
                    f"{average_ppe:.1f}%"
                )

                col3.metric("High/Critical Risk", int(high_risk))

                col4.metric("PPE Non-Compliant", int(non_compliant))

                st.divider()

                # Search and filter workers
                st.markdown("### Search and Filter Workers")

                search_id = st.text_input(
                    "Search by Worker ID"
                )

                departments = ["All"] + sorted(
                    workers["Department"].dropna().unique().tolist()
                )

                selected_department = st.selectbox(
                    "Department",
                    departments
                )

                risk_levels = ["All"] + sorted(
                    workers["Risk_Level"].dropna().unique().tolist()
                )

                selected_risk = st.selectbox(
                    "Risk Level",
                    risk_levels
                )

                filtered_workers = workers.copy()

                if search_id.strip():
                    filtered_workers = filtered_workers[
                        filtered_workers["Worker_ID"].astype(str)
                        .str.contains(
                            search_id.strip(),
                            case=False,
                            na=False
                        )
                    ]

                if selected_department != "All":
                    filtered_workers = filtered_workers[
                        filtered_workers["Department"]
                        == selected_department
                    ]

                if selected_risk != "All":
                    filtered_workers = filtered_workers[
                        filtered_workers["Risk_Level"]
                        == selected_risk
                    ]

                st.write(
                    f"Workers found: {len(filtered_workers)}"
                )

                st.dataframe(
                    filtered_workers,
                    use_container_width=True,
                    hide_index=True
                )

            except FileNotFoundError:
                st.error(
                    "Could not find workers.csv. "
                    "Check the DATA_FOLDER path."
                )

            except KeyError as error:
                st.error(
                    f"Column not found: {error}. "
                    "Check the workers.csv column names."
                )

        elif page == "Risk Assessment":
            import views.alerts as risk_page
            importlib.reload(risk_page)  # Forces Python to fresh-load the module every time!
            
            if hasattr(risk_page, "render"):
                risk_page.render(DATA_FOLDER)
            else:
                st.write("Risk assessment module loaded.")

        elif page == "Reports":
            import views.risk_assessment as notifications_page
            importlib.reload(notifications_page)  # Forces Python to fresh-load the module every time!
            
            if hasattr(notifications_page, "render"):
                notifications_page.render(DATA_FOLDER)
            else:
                st.write("Risk assessment module loaded.")

        elif page == "Safety Incidents":
            import views.incidents as incidents_page
            importlib.reload(incidents_page)
            
            if hasattr(incidents_page, "render"):
                incidents_page.render(DATA_FOLDER)
            else:
                st.write("Safety Incidents module loaded.")

        elif page == "Equipment":
            import views.equipment_app as equipment_page
            importlib.reload(equipment_page)  # Forces Python to fresh-load
            
            if hasattr(equipment_page, "render"):
                equipment_page.render(DATA_FOLDER)
            else:
                st.write("equipment_app module loaded.")

        elif page == "Manage Users":
            import views.manage_users as manage_page
            importlib.reload(manage_page)
            
            if hasattr(manage_page, "render"):
                manage_page.render(DATA_FOLDER)
            else:
                st.write("Manage Users module loaded.")
        if st.sidebar.button("Log out"):
           st.session_state.logged_in = False
           st.session_state.username = ""
           st.session_state.role = ""
           st.rerun()