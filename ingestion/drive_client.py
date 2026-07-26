"""OAuth-authenticated Google Drive client: list and download files from one folder."""
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

CREDENTIALS_PATH = "credentials.json"
TOKEN_PATH = "token.json"

# TODO(kun): 對照你在「三個為什麼」Q2 的討論，這裡該填 read-only 還是
# read-write 的 scope？(https://developers.google.com/drive/api/guides/api-specific-auth)
SCOPES = [""]

# TODO(kun): 填你在 GCP Console 步驟 6 建的資料夾 ID。
FOLDER_ID = ""


def get_credentials() -> Credentials:
    """Load cached token if valid, else run the OAuth consent flow once."""
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # TODO(kun): 用 InstalledAppFlow.from_client_secrets_file(...) 建立 flow，
            # 再呼叫 flow.run_local_server(port=0) 跳出瀏覽器完成授權。
            raise NotImplementedError

        with open(TOKEN_PATH, "w") as token_file:
            token_file.write(creds.to_json())

    return creds


def list_files(service, folder_id: str) -> list[dict]:
    """Return [{id, name}, ...] for files directly inside folder_id."""
    # TODO(kun): 用 service.files().list(q=..., fields=...) 查詢，
    # q 要用 "'<folder_id>' in parents" 把範圍鎖在這個資料夾。
    raise NotImplementedError


def download_file(service, file_id: str, destination: str) -> None:
    """Download file_id to destination on local disk."""
    # TODO(kun): 用 service.files().get_media(fileId=file_id) 搭配
    # MediaIoBaseDownload 分段寫入 destination。
    raise NotImplementedError


def main():
    creds = get_credentials()
    service = build("drive", "v3", credentials=creds)
    files = list_files(service, FOLDER_ID)
    print(f"found {len(files)} file(s) in folder {FOLDER_ID}")
    for f in files:
        print(f" - {f['name']} ({f['id']})")


if __name__ == "__main__":
    main()
