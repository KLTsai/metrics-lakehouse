"""T1.2:drive_client 的純邏輯(檔案比對)與 SA 憑證建構參數。

find_file_id 是 download_day() 逐租戶逐表挑檔的核心比對邏輯,抽成純函式
(輸入 list_files() 的回傳形狀,不碰 Drive API)方便不 mock 網路就測到。
找不到時的錯誤訊息要點名租戶+表+檔案日(任務卡驗證標準 #3:大聲失敗、
講得出缺什麼),所以訊息內容本身也是斷言對象,不只是「有沒有 raise」。
"""

import pytest

from ingestion.drive_client import SCOPES, find_file_id, get_credentials, resolve_tenant_folders


def test_find_file_id_matches_by_exact_filename():
    files = [
        {"id": "id-a", "name": "transaction_detail_2026-01-01.csv"},
        {"id": "id-b", "name": "accounts_receivable_2026-01-01.csv"},
    ]
    assert find_file_id(files, tenant="alpha", table="accounts_receivable", file_date="2026-01-01") == "id-b"


def test_find_file_id_raises_with_tenant_table_date_when_missing():
    files = [{"id": "id-a", "name": "transaction_detail_2026-01-01.csv"}]

    with pytest.raises(FileNotFoundError) as exc_info:
        find_file_id(files, tenant="beta", table="accounts_receivable", file_date="2026-02-01")

    message = str(exc_info.value)
    assert "beta" in message
    assert "accounts_receivable" in message
    assert "2026-02-01" in message


def test_find_file_id_does_not_partial_match_other_tables():
    # transaction_detail 不該被 accounts_receivable 的查詢誤配到
    files = [{"id": "id-a", "name": "transaction_detail_2026-01-01.csv"}]

    with pytest.raises(FileNotFoundError):
        find_file_id(files, tenant="alpha", table="accounts_receivable", file_date="2026-01-01")


def test_resolve_tenant_folders_maps_name_to_id():
    landing_children = [
        {"id": "folder-alpha", "name": "alpha"},
        {"id": "folder-beta", "name": "beta"},
        {"id": "folder-other", "name": "some-unrelated-folder"},
    ]
    assert resolve_tenant_folders(landing_children, ["alpha", "beta"]) == {
        "alpha": "folder-alpha",
        "beta": "folder-beta",
    }


def test_resolve_tenant_folders_raises_naming_missing_tenants():
    landing_children = [{"id": "folder-alpha", "name": "alpha"}]

    with pytest.raises(FileNotFoundError) as exc_info:
        resolve_tenant_folders(landing_children, ["alpha", "beta"])

    assert "beta" in str(exc_info.value)


def test_get_credentials_reads_key_file_with_readonly_scope(monkeypatch, tmp_path):
    key_path = tmp_path / "fake-key.json"
    key_path.write_text("{}")
    monkeypatch.setattr("ingestion.drive_client.SERVICE_ACCOUNT_KEY_PATH", str(key_path))

    captured = {}

    def fake_from_service_account_file(path, scopes):
        captured["path"] = path
        captured["scopes"] = scopes
        return "fake-credentials"

    monkeypatch.setattr(
        "ingestion.drive_client.service_account.Credentials.from_service_account_file",
        fake_from_service_account_file,
    )

    creds = get_credentials()

    assert creds == "fake-credentials"
    assert captured["path"] == str(key_path)
    assert captured["scopes"] == SCOPES
