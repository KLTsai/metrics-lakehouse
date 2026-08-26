"""Service-account-authenticated Google Drive client: list and download files from one folder."""
import os

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# 容器內由 compose 覆寫成掛載路徑;host 上 uv run 時吃這個預設值(repo 根)。
SERVICE_ACCOUNT_KEY_PATH = os.environ.get("SERVICE_ACCOUNT_KEY_PATH", "service-account-key.json")

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

FOLDER_ID = "1DgrZIkA2Pis-sYz_2v3BDj4I0YOk75xh"  # 我的雲端硬碟/lakehouse/landing


def get_credentials() -> service_account.Credentials:
    """Build service-account credentials from the key file (ADR 0003; no browser, no expiry)."""
    return service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_KEY_PATH, scopes=SCOPES)


def list_files(service, folder_id: str) -> list[dict]:
    """Return [{id, name}, ...] for files directly inside folder_id."""
    results = service.files().list(q=f"'{folder_id}' in parents", fields="files(id, name)").execute()
    return results.get("files", [])


def resolve_tenant_folders(landing_children: list[dict], tenants: list[str]) -> dict[str, str]:
    """Map tenant name -> folder id from a list_files(landing) result.

    Raises FileNotFoundError naming every missing tenant instead of silently
    downloading fewer tenants than expected.
    """
    by_name = {f["name"]: f["id"] for f in landing_children}
    missing = [t for t in tenants if t not in by_name]
    if missing:
        raise FileNotFoundError(f"landing 資料夾底下找不到租戶子資料夾:{missing}")
    return {t: by_name[t] for t in tenants}


def find_file_id(files: list[dict], *, tenant: str, table: str, file_date: str) -> str:
    """Pick the file id matching `{table}_{file_date}.csv` out of a list_files() result.

    Raises FileNotFoundError naming tenant/table/file_date instead of returning None —
    a silently-missing file is the exact upstream failure mode this pipeline must not repeat.
    """
    filename = f"{table}_{file_date}.csv"
    for f in files:
        if f["name"] == filename:
            return f["id"]
    raise FileNotFoundError(f"租戶 {tenant} 的 {table} 表在檔案日 {file_date} 找不到檔案(預期檔名 {filename})")


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
