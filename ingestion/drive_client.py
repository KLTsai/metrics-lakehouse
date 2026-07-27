"""OAuth-authenticated Google Drive client: list and download files from one folder."""
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

CREDENTIALS_PATH = "credentials.json"
TOKEN_PATH = "token.json"

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

FOLDER_ID = "1uPwb7gFdMZrMBwxQrndwueZ5xkJycFTK"


def get_credentials() -> Credentials:
    """Load cached token if valid, else run the OAuth consent flow once."""
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_PATH, "w") as token_file:
            token_file.write(creds.to_json())

    return creds


def list_files(service, folder_id: str) -> list[dict]:
    """Return [{id, name}, ...] for files directly inside folder_id."""
    results = service.files().list(q=f"'{folder_id}' in parents", fields="files(id, name)").execute()
    return results.get("files", [])


def download_file(service, file_id: str, destination: str) -> None:
    """Download file_id to destination on local disk."""
    request = service.files().get_media(fileId=file_id)

    with open(destination, "wb") as f:
        downloader = MediaIoBaseDownload(f, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()


def main():
    creds = get_credentials()
    service = build("drive", "v3", credentials=creds)
    files = list_files(service, FOLDER_ID)
    print(f"found {len(files)} file(s) in folder {FOLDER_ID}")
    for f in files:
        print(f" - {f['name']} ({f['id']})")


if __name__ == "__main__":
    main()
