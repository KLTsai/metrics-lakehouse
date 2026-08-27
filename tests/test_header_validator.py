"""T1.3 驗票口單元測試:表頭比對只看欄位名稱組成,不管順序、不管值。

契約來源同產生器(generator/schema.py),避免另外手抄一份欄名清單。
"""

import pytest

from generator.schema import ACCOUNTS_RECEIVABLE, TRANSACTION_DETAIL
from ingestion.header_validator import HeaderDriftError, validate_header


def _header(table, drop=None, add=None):
    fields = [f.name_zh for f in table.fields if f.name_zh != drop]
    if add:
        fields.append(add)
    return fields


def test_matching_header_passes():
    validate_header(TRANSACTION_DETAIL, _header(TRANSACTION_DETAIL))


def test_column_order_does_not_matter():
    # CONTEXT.md「欄位名稱漂移」只界定名稱/組成,不含順序
    validate_header(TRANSACTION_DETAIL, list(reversed(_header(TRANSACTION_DETAIL))))


def test_renamed_column_reports_both_missing_and_extra():
    header = _header(TRANSACTION_DETAIL, drop="客戶編號", add="客戶代碼")
    with pytest.raises(HeaderDriftError) as exc:
        validate_header(TRANSACTION_DETAIL, header)
    msg = str(exc.value)
    assert "客戶編號" in msg  # 缺欄
    assert "客戶代碼" in msg  # 多欄


def test_dropped_column_reports_missing_only():
    header = _header(TRANSACTION_DETAIL, drop="備註說明")
    with pytest.raises(HeaderDriftError) as exc:
        validate_header(TRANSACTION_DETAIL, header)
    assert "備註說明" in str(exc.value)
    assert "多欄:無" in str(exc.value)


def test_added_column_reports_extra_only():
    header = _header(ACCOUNTS_RECEIVABLE) + ["新欄位"]
    with pytest.raises(HeaderDriftError) as exc:
        validate_header(ACCOUNTS_RECEIVABLE, header)
    assert "新欄位" in str(exc.value)
    assert "缺欄:無" in str(exc.value)
