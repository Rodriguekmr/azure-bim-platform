# # ----------------------------
# # RAW DATA EXPANDER
# # ----------------------------

import streamlit as st
st.write("Streamlit version:", st.__version__)
st.stop()
import pandas as pd
import os

from dotenv import load_dotenv
from azure.data.tables import TableServiceClient
from azure.storage.blob import BlobServiceClient
from st_aggrid import AgGrid, GridOptionsBuilder
#-------for authentication in streamlit cloud-------
# from auth import get_auth_url, process_login

# ==================================================
# PAGE CONFIG
# ==================================================

st.set_page_config(
    page_title="Azure BIM Platform",
    page_icon="🏗️",
    layout="wide"
)

# ==================================================
# ENVIRONMENT VARIABLES
# ==================================================

#-------------------------------------------------------------
# load_dotenv()

# if "authenticated" not in st.session_state:
#     st.session_state.authenticated = False

# if "user_email" not in st.session_state:
    
#     user_email = ""

# if "user_id" not in st.session_state:
    
#     user_id = ""

# CONNECTION_STRING = os.getenv(
#     "AZURE_STORAGE_CONNECTION_STRING"
# )

load_dotenv()

#-----------------------------------------------------------
# ==================================================
# SESSION STATE INITIALIZATION
# ==================================================

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "user_email" not in st.session_state:
    st.session_state.user_email = ""

if "user_id" not in st.session_state:
    st.session_state.user_id = ""

if "groups" not in st.session_state:
    st.session_state.groups = []
#-----------------------------------------------------------
def get_setting(name):


    if name in st.secrets:

        return st.secrets[name]

    return os.getenv(name)


CONNECTION_STRING = get_setting(
    "AZURE_STORAGE_CONNECTION_STRING"
)

blob_service_client = BlobServiceClient.from_connection_string(
    CONNECTION_STRING
)
TABLE_NAME = "bimmetadata"

if not CONNECTION_STRING:
    raise ValueError(
        "CONNECTION_STRING is None — check your .env file"
    )

# ==================================================
# MICROSOFT ENTRA AUTHENTICATION
# ==================================================

# # --------------------------------------------
# # Login screen
# # --------------------------------------------

# import streamlit as st
if not st.user.is_logged_in:

    st.title("🏗️ Azure BIM Platform")

    st.markdown(
        """
        Welcome to the BIM Workflow Automation Platform.

        Please sign in to continue.
        """
    )

    if st.button("Sign in with Microsoft"):
        st.login()

    st.stop()


user_email = st.user["preferred_username"]
user_id = st.user["oid"]

groups = st.user["groups"]

BIMCOORDINATOR_GROUP = "fc939939-19bf-4fe0-aeac-158fb4390448"
VIEWER_GROUP = "8bf75d23-5b5f-4c55-9530-e00091a53108"
ARCHITECT_GROUP = "602dcf78-16ef-4172-8e86-7ef4bc832ac9"

is_admin = BIMCOORDINATOR_GROUP in groups

is_architect = ARCHITECT_GROUP in groups

is_viewer = VIEWER_GROUP in groups

can_upload = is_admin or is_architect

can_download = is_admin or is_architect

can_delete = is_admin
# ==================================================
# MICROSOFT ENTRA AUTHENTICATION
# ==================================================

# process_login()

# if not st.session_state.get("authenticated", False):

#     st.title("🏗️ Azure BIM Platform")

#     st.markdown("""
#     Welcome to the BIM Workflow Automation Platform.

#     Please sign in to continue.
#     """)

#     login_url = get_auth_url()

#     st.link_button(
#         "Sign in with Microsoft",
#         login_url
#     )

#     st.stop()

#     # # THEN USE IT
#     # st.markdown(
#     #     f"""
#     #     <a href="{login_url}" target="_self">
#     #         <button style="
#     #             background:#F63366;
#     #             color:white;
#     #             border:none;
#     #             padding:0.6em 1.2em;
#     #             border-radius:0.5em;
#     #             cursor:pointer;
#     #             font-size:16px;">
#     #             Sign in with Microsoft
#     #         </button>
#     #     </a>
#     #     """,
#     #     unsafe_allow_html=True,
#     # )

#     # st.stop()


# user_email = st.session_state.user_email

# user_id = st.session_state.user_id

# groups = st.session_state.groups


# BIMCOORDINATOR_GROUP = "fc939939-19bf-4fe0-aeac-158fb4390448"

# VIEWER_GROUP = "8bf75d23-5b5f-4c55-9530-e00091a53108"

# ARCHITECT_GROUP = "602dcf78-16ef-4172-8e86-7ef4bc832ac9"


# is_admin = BIMCOORDINATOR_GROUP in groups

# is_architect = ARCHITECT_GROUP in groups

# is_viewer = VIEWER_GROUP in groups


# can_upload = is_admin or is_architect

# can_download = is_admin or is_architect

# can_delete = is_admin

# ==================================================
# HEADER
# ==================================================

header_left, header_right = st.columns([5, 2])

with header_left:
    st.title("🏗️ Azure BIM Platform")

with header_right:

    st.caption("Logged in as")

    st.text(
        
        user_email
    )

    
    if st.button("Logout"):
        st.logout()
    # if st.button("Logout"):

    #     st.session_state.authenticated = False
    #     st.session_state.user_email = ""
    #     st.session_state.user_id = ""
    #     st.session_state.groups = []

    #     st.rerun()

# ==================================================
# NAVIGATION
# ==================================================
if can_upload:
    pages = [
        "Upload BIM Files",
        "Dashboard"
    ]
else:
    pages = [
        "Dashboard"
    ]

page = st.sidebar.selectbox(
    "Navigation",
    pages
)

# ==================================================
# FILE UPLOAD PAGE
# ==================================================
if page == "Upload BIM Files":

    st.header("Upload BIM Files")

    col1, col2 = st.columns([2, 3])

    with col1:
        discipline = st.selectbox(
            "Discipline",
            [
                "architecture",
                "structure",
                "mep",
                "electrical",
                "civil"
            ]
        )

    col1, col2 = st.columns([2, 3])

    with col1:

        uploaded_files = st.file_uploader(
            "BIM Files",
            type=["rvt","ifc","pdf","dwg","pln"],
            accept_multiple_files=True
        )

    from datetime import datetime

    if st.button("Send Files"):

        if uploaded_files:

            uploaded_count = 0

            table_service = TableServiceClient.from_connection_string(
                CONNECTION_STRING
            )

            table_client = table_service.get_table_client(TABLE_NAME)

            for uploaded_file in uploaded_files:

                try:

                    filename = uploaded_file.name

                    name, ext = os.path.splitext(filename)

                    version = 1

                    entities = table_client.list_entities()

                    for entity in entities:

                        if entity.get("filename") == filename:

                            if entity.get("version", 1) >= version:

                                version = entity["version"] + 1

                    blob_name = f"{name}_v{version}{ext}"

                    blob_client = blob_service_client.get_blob_client(
                        container=discipline,
                        blob=blob_name
                    )

                    blob_client.upload_blob(
                        uploaded_file.getvalue(),
                        overwrite=False,
                        metadata={
                            "uploaded_by": user_email,
                            "user_id": user_id,
                        }
                    )

                    st.write(f"✅ Uploaded: {blob_name}")

                    uploaded_count += 1

                except Exception as e:

                    st.error(f"❌ Failed: {uploaded_file.name}")
                    st.exception(e)

            st.success(f"{uploaded_count} file(s) uploaded.")

    st.stop()
  
# ==================================================
# DASHBOARD PAGE
# ==================================================

if page == "Dashboard":

    # ----------------------------------------------
    # CONNECT TO AZURE TABLE
    # ----------------------------------------------

    service = TableServiceClient.from_connection_string(
        CONNECTION_STRING
    )

    table_client = service.get_table_client(
        TABLE_NAME
    )

    entities = list(
        table_client.list_entities()
    )

    if not entities:

        st.warning(
            "No BIM metadata found in table."
        )

        st.stop()

    df = pd.DataFrame(entities)
    
    # ----------------------------------------------
    # NORMALIZE COLUMN NAMES
    # ----------------------------------------------

    df.columns = [
        c.lower()
        for c in df.columns
    ]

    if "partitionkey" in df.columns:
        df.drop(columns=["partitionkey"], inplace=True)

    if "rowkey" in df.columns:

        df.rename(
            columns={
                "rowkey": "id"
            },
            inplace=True
        )

    # ----------------------------------------------
    # CLEAN DATA
    # ----------------------------------------------

    if "upload_date" in df.columns:

        df["upload_date"] = ( 
            pd.to_datetime(
                df["upload_date"],
                utc=True,
                errors="coerce"
            )
           .dt.tz_convert("Europe/Warsaw")
        )
    display_df = df.copy()

    if "upload_date" in display_df.columns:

        display_df["upload_date"] = (
            display_df["upload_date"]
            .dt.strftime("%d/%m/%Y %H:%M:%S")
        )

    # ----------------------------------------------
    # DASHBOARD HEADER
    # ----------------------------------------------

    st.header("BIM Metadata Dashboard")

    st.metric(
        "Total Files",
        len(df)
    )

    st.divider()

    # ----------------------------------------------
    # FILE TABLE
    # ----------------------------------------------
    
    st.subheader("Uploaded Files")

    display_df = display_df.reset_index(drop=True)

    display_df.insert(0, "nr", display_df.index + 1)

    display_df["is_latest"] = display_df["is_latest"].map({
        True: "✅",
        False: ""
    })

    table_df = display_df[
        [
            "nr",
            "filename",
            "filetype",
            "discipline",
            "category",
            "upload_date",
            "uploaded_by",
            "user_id",
            "version",
            "is_latest",
            "id",
            "blob_name",
            "container"
        ]
    ].copy()

    gb = GridOptionsBuilder.from_dataframe(table_df)

    gb.configure_default_column(
        sortable=True,
        filter=True,
        resizable=True,
        cellStyle={
            "textAlign": "center"
        }
    )

    if is_viewer:

        gb.configure_selection(
            selection_mode="disabled"
        )

    else:

        gb.configure_selection(
            selection_mode="single",
            use_checkbox=True
        )
   
    gb.configure_column("nr", width=100)

    gb.configure_column("id", hide=True)
    gb.configure_column("blob_name", hide=True)
    gb.configure_column("container", hide=True)
    gb.configure_column("Action", hide=True)
    
    table_height = min(400, 30 * len(table_df) + 16)

    grid = AgGrid(
    table_df,
    gridOptions=gb.build(),
    height=table_height,
    fit_columns_on_grid_load=True,  
    )

    selected = grid.selected_data

    if (
        selected is not None
        and not selected.empty
    ):

        selected_id = selected.iloc[0]["id"]

        selected_row = df.loc[
            df["id"] == selected_id
        ].iloc[0]

        if not is_viewer:

            st.divider()

            st.subheader("Details / Actions")

            st.write("**Filename:**", selected_row["filename"])
            st.write("**Version:**", selected_row["version"])
            st.write("**Uploaded by:**", selected_row["uploaded_by"])
            st.write("**Upload date:**", selected_row["upload_date"])

            if can_download:

                container = selected_row.get("container")
                blob_name = selected_row.get("blob_name")

                if pd.isna(container) or pd.isna(blob_name):

                    st.error(
                        "This file was uploaded before versioning was implemented and cannot be downloaded."
                    )

                else:

                    blob_client = blob_service_client.get_blob_client(
                        container=container,
                        blob=blob_name
                    )

                    from azure.core.exceptions import ResourceNotFoundError

                    try:

                        file_bytes = blob_client.download_blob().readall()

                        st.download_button(
                            "⬇ Download File",
                            data=file_bytes,
                            file_name=selected_row["filename"],
                            mime="application/octet-stream"
                        )

                    except ResourceNotFoundError:

                        st.warning(
                            "⚠️ This file is no longer available on the server."
                        )

                        st.info(
                            "The metadata still exists in the dashboard, but the file has been removed from Azure Storage."
                        )


                    if can_delete:

                        if st.button("🗑 Delete"):

                            try:

                                blob_client.delete_blob()

                                table_client.delete_entity(
                                    partition_key=selected_row["discipline"],
                                    row_key=selected_row["id"]
                                )

                                st.success("File deleted.")

                                st.rerun()

                            except ResourceNotFoundError:

                                st.warning(
                                    "⚠️ This file has already been removed from Azure Storage."
                                )
                                st.session_state["remove_metadata"] = True

                                
                        if st.session_state.get("remove_metadata", False):

                            if st.button(
                                "Remove metadata only",
                                key=f"remove_{selected_row['id']}"
                            ):

                                table_client.delete_entity(
                                    partition_key=selected_row["discipline"],
                                    row_key=selected_row["id"]
                                )

                                st.session_state["remove_metadata"] = False

                                st.success("Metadata removed.")

                                st.rerun()

        else:

            st.info("Viewer access")
    # ----------------------------------------------
    # ANALYTICS
    # ----------------------------------------------

    col1, col2 = st.columns(2)

    with col1:

        if "discipline" in df.columns:

            st.subheader("Uploads by Discipline")

            disciplines = [
                "Architecture",
                "Structure",
                "MEP",
                "Electrical",
                "Civil"
            ]

            counts = (
                df["discipline"]
                .value_counts()
                .reindex(disciplines, fill_value=0)
            )

            st.bar_chart(counts)

    with col2:

        if "filetype" in df.columns:

            st.subheader("File Types")

            filetypes = [
                "RVT",
                "IFC",
                "DWG",
                "PDF",
                "PLN"
            ]

            filetype_counts = (
                df["filetype"]
                .value_counts()
                .reindex(filetypes, fill_value=0)
            )

            st.bar_chart(filetype_counts)

    # ----------------------------------------------
    # UPLOAD TREND
    # ----------------------------------------------

    if "upload_date" in df.columns:

        st.subheader("Uploads Over Time")

        uploads = (
            df.groupby(
                df["upload_date"].dt.date
            )
            .size()
        )

        st.line_chart(
            uploads
        )

    # ----------------------------------------------
    # TOP CONTRIBUTORS
    # ----------------------------------------------

    if "uploaded_by" in df.columns:

        st.subheader("Top Contributors")

        st.bar_chart(
            df["uploaded_by"].value_counts()
        )

    else:

        st.info(
            "No uploader information available."
        )

    # ----------------------------------------------
    # RAW DATA
    # ----------------------------------------------

    with st.expander("Raw Azure Table Data"):

        st.dataframe(
            df,
            use_container_width=True
        )