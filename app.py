import streamlit as st
import pandas as pd
from azure.data.tables import TableServiceClient

from azure.storage.blob import BlobServiceClient
# ----------------------------
# CONFIG
# ----------------------------
from dotenv import load_dotenv
import os

load_dotenv()  # must be before os.environ.get()

CONNECTION_STRING = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")

# Add this to confirm it loaded
if not CONNECTION_STRING:
    raise ValueError("CONNECTION_STRING is None — check your .env file")
TABLE_NAME = "bimmetadata"

# ----------------------------
# CONNECT TO TABLE
# ----------------------------
service = TableServiceClient.from_connection_string(CONNECTION_STRING)
table_client = service.get_table_client(TABLE_NAME)

# Fetch data
entities = list(table_client.list_entities())

if not entities:
    st.warning("No BIM metadata found in table.")
    st.stop()

df = pd.DataFrame(entities)

# Normalize column names (VERY IMPORTANT for Azure Tables)
df.columns = [c.lower() for c in df.columns]

# Ensure correct column names exist
if "partitionkey" in df.columns:
    df.rename(columns={"partitionkey": "discipline"}, inplace=True)

if "rowkey" in df.columns:
    df.rename(columns={"rowkey": "id"}, inplace=True)

# ----------------------------
# CLEAN DATA
# ----------------------------
df["upload_date"] = pd.to_datetime(df["upload_date"], errors="coerce")

# ----------------------------
# UI
# ----------------------------
page = st.sidebar.selectbox(
    "Navigation",
    [
        "Upload BIM Files",
        "Dashboard" 
    ]
)

st.title("🏗 BIM Metadata Dashboard")
# ----------------------------
# FILE UPLOAD PAGE
# ----------------------------

if page == "Upload BIM Files":

    st.header("Upload BIM Files")

    discipline = st.selectbox(
        "Select Discipline",
        [
            "architecture",
            "structure",
            "mep",
            "electrical",
            "civil"
        ]
    )

    uploaded_files = st.file_uploader(
        "Choose BIM files",
        type=["rvt", "ifc", "pdf", "dwg"],
        accept_multiple_files=True
    )

    if st.button("Upload Files"):

        if uploaded_files:

            blob_service_client = BlobServiceClient.from_connection_string(CONNECTION_STRING)

            for uploaded_file in uploaded_files:

                blob_client = blob_service_client.get_blob_client(
                    container=discipline,
                    blob=uploaded_file.name
                )

                blob_client.upload_blob(
                    uploaded_file.getvalue(),
                    overwrite=True
                )

            st.success(
                f"{len(uploaded_files)} file(s) uploaded successfully."
            )

    st.stop()

st.metric("Total Files", len(df))

st.divider()

# ----------------------------
# TABLE VIEW
# ----------------------------
st.subheader("Uploaded Files")
st.dataframe(df[[
    "filename",
    "filetype",
    "category",
    "discipline",
    "upload_date"
]])

# ----------------------------
# ANALYTICS
# ----------------------------
st.subheader("Uploads by Discipline")
st.bar_chart(df["discipline"].value_counts())

st.subheader("File Types Distribution")
st.bar_chart(df["filetype"].value_counts())

st.subheader("Uploads Over Time")
time_df = df.groupby(df["upload_date"].dt.date).size()
st.line_chart(time_df)

# ----------------------------
# RAW DATA EXPANDER
# ----------------------------
with st.expander("Raw Data"):
    st.write(df)