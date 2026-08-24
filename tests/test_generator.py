"""T0.5 驗證:合成資料產生器的四類髒資料注入為精確相等斷言。

驗證標準(handoff-T0.5-signoff.md §3,rate=5%):
1. 缺值:缺值池欄位空儲存格數 == floor(required欄位數 × 基底列數 × rate)
2. 重複:總列數 − 相異主鍵數 == floor(基底列數 × rate)
3. 漂移:decimal/datetime 欄位型別解析失敗(非空)儲存格數
        == floor((decimal+datetime欄位數) × 基底列數 × rate)
4. 遲到:出現在非自身批次檔案的列數 == floor(基底列數 × rate)
5. 同 seed 跑兩次 → byte-identical

遲到偵測依據主鍵內嵌的批次日期(YYYYMMDD),不用日期欄——日期欄可能被
缺值/漂移注入命中,主鍵則保證不被注入(缺值池排除主鍵)。
期望值的 floor(分母 × rate) 與實作用同一算式,浮點行為一致故可精確相等。
"""

import csv
import math
import re
from datetime import date, datetime
from pathlib import Path

import pytest

from generator.generate import Rates, generate_all
from generator.schema import DATETIME, DECIMAL, TABLES

TENANTS = ["alpha", "beta"]
ROWS = 200
BATCHES = 4
START = date(2026, 1, 1)
SEED = 42
RATE = 0.05

# 嚴格型別解析:乾淨資料一定通過、九種漂移樣式一定失敗
_STRICT_DECIMAL_RE = re.compile(r"^-?\d+(\.\d+)?$")


def _parses_as(kind: str, value: str) -> bool:
    if kind == DECIMAL:
        return bool(_STRICT_DECIMAL_RE.match(value))
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except ValueError:
        return False


_PK_DATE_RE = re.compile(r"-(\d{8})-")


def _pk_batch_date(pk: str) -> date:
    return datetime.strptime(_PK_DATE_RE.search(pk).group(1), "%Y%m%d").date()


@pytest.fixture(scope="module")
def out_dir(tmp_path_factory) -> Path:
    out = tmp_path_factory.mktemp("gen")
    generate_all(
        out_dir=out,
        tenants=TENANTS,
        rows=ROWS,
        batches=BATCHES,
        start_date=START,
        seed=SEED,
        rates=Rates(missing=RATE, duplicate=RATE, drift=RATE, late=RATE),
    )
    return out


def _read_files(out: Path, tenant: str, table) -> list[tuple[date, list[dict]]]:
    """回傳 [(檔名批次日期, [row dict(name_en → value)])],依日期排序。"""
    result = []
    for path in sorted((out / tenant).glob(f"{table.name}_*.csv")):
        file_date = date.fromisoformat(path.stem.removeprefix(f"{table.name}_"))
        with path.open(encoding="utf-8-sig", newline="") as fh:
            reader = csv.reader(fh)
            header = next(reader)
            assert header == [f.name_zh for f in table.fields], path
            en = [f.name_en for f in table.fields]
            rows = [dict(zip(en, row, strict=True)) for row in reader]
        result.append((file_date, rows))
    return result


def _all_rows(files):
    return [row for _, rows in files for row in rows]


def _case_ids():
    return [(t, table) for t in TENANTS for table in TABLES.values()]


@pytest.mark.parametrize(
    "tenant,table", _case_ids(), ids=lambda v: v if isinstance(v, str) else v.name
)
class TestInjectionExactCounts:
    def test_missing_cells(self, out_dir, tenant, table):
        rows = _all_rows(_read_files(out_dir, tenant, table))
        required = sum(1 for f in table.fields if f.required)
        expected = math.floor(required * ROWS * RATE)
        pool_empty = sum(1 for r in rows for c in table.missing_pool if r[c] == "")
        assert pool_empty == expected
        # 缺值只落在缺值池;其他欄位(含主鍵)不得為空
        outside = [
            f.name_en
            for f in table.fields
            if f.name_en not in table.missing_pool
            for r in rows
            if r[f.name_en] == ""
        ]
        assert outside == []

    def test_duplicate_rows(self, out_dir, tenant, table):
        rows = _all_rows(_read_files(out_dir, tenant, table))
        expected = math.floor(ROWS * RATE)
        assert len(rows) == ROWS + expected
        distinct_pk = len({r[table.primary_key] for r in rows})
        assert len(rows) - distinct_pk == expected

    def test_format_drift_cells(self, out_dir, tenant, table):
        rows = _all_rows(_read_files(out_dir, tenant, table))
        typed = [f for f in table.fields if f.kind in (DECIMAL, DATETIME)]
        expected = math.floor(len(typed) * ROWS * RATE)
        bad = sum(
            1
            for r in rows
            for f in typed
            if r[f.name_en] != "" and not _parses_as(f.kind, r[f.name_en])
        )
        assert bad == expected

    def test_late_rows(self, out_dir, tenant, table):
        files = _read_files(out_dir, tenant, table)
        expected = math.floor(ROWS * RATE)
        late = [
            (file_date, row)
            for file_date, rows in files
            for row in rows
            if _pk_batch_date(row[table.primary_key]) != file_date
        ]
        assert len(late) == expected
        # 遲到 = 延後,只准出現在「晚於」自身批次的檔案
        assert all(
            _pk_batch_date(row[table.primary_key]) < file_date
            for file_date, row in late
        )


def test_same_seed_byte_identical(tmp_path):
    kwargs = dict(
        tenants=["alpha"],
        rows=50,
        batches=3,
        start_date=START,
        seed=7,
        rates=Rates(missing=RATE, duplicate=RATE, drift=RATE, late=RATE),
    )
    a, b = tmp_path / "a", tmp_path / "b"
    generate_all(out_dir=a, **kwargs)
    generate_all(out_dir=b, **kwargs)
    files_a = sorted(p.relative_to(a) for p in a.rglob("*.csv"))
    files_b = sorted(p.relative_to(b) for p in b.rglob("*.csv"))
    assert files_a == files_b and files_a
    for rel in files_a:
        assert (a / rel).read_bytes() == (b / rel).read_bytes(), rel


def test_output_layout_and_bom(out_dir):
    for tenant in TENANTS:
        for table in TABLES.values():
            paths = sorted((out_dir / tenant).glob(f"{table.name}_*.csv"))
            assert len(paths) == BATCHES
            for path in paths:
                assert re.fullmatch(
                    rf"{table.name}_\d{{4}}-\d{{2}}-\d{{2}}\.csv", path.name
                )
                assert path.read_bytes()[:3] == b"\xef\xbb\xbf"


def test_cli_smoke(tmp_path):
    from generator.cli import main

    main(
        [
            "--out",
            str(tmp_path),
            "--tenants",
            "t1",
            "--rows",
            "40",
            "--batches",
            "3",
            "--start-date",
            "2026-02-01",
            "--seed",
            "9",
        ]
    )
    written = sorted(p.name for p in (tmp_path / "t1").glob("*.csv"))
    assert written == [
        "accounts_receivable_2026-02-01.csv",
        "accounts_receivable_2026-02-02.csv",
        "accounts_receivable_2026-02-03.csv",
        "transaction_detail_2026-02-01.csv",
        "transaction_detail_2026-02-02.csv",
        "transaction_detail_2026-02-03.csv",
    ]
