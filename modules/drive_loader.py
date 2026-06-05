import io
from datetime import datetime
import streamlit as st
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload


SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]


def get_drive_service():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=SCOPES,
    )

    service = build("drive", "v3", credentials=creds)
    return service


def expected_ems_filename(selected_date):
    return selected_date.strftime("Consumption_%d%m%Y_D.xls")


def find_file_in_drive(folder_id, file_name):
    service = get_drive_service()

    query = (
        f"'{folder_id}' in parents and "
        f"name = '{file_name}' and "
        f"trashed = false"
    )

    result = service.files().list(
        q=query,
        fields="files(id, name, mimeType, modifiedTime)",
        pageSize=10,
        supportsAllDrives=True,
        includeItemsFromAllDrives=True,
    ).execute()

    files = result.get("files", [])

    if not files:
        return None

    return files[0]


def download_drive_file(file_id):
    service = get_drive_service()

    request = service.files().get_media(fileId=file_id)

    file_buffer = io.BytesIO()
    downloader = MediaIoBaseDownload(file_buffer, request)

    done = False
    while not done:
        status, done = downloader.next_chunk()

    file_buffer.seek(0)
    return file_buffer
