"""CLI:uv run python -m generator [options]。

預設值即 T0.5 驗收情境:兩租戶、各表 500 基底列、5 個日批次、
四類髒資料各 5%、固定 seed(同 seed 重跑輸出 byte-identical)。
"""

import argparse
from datetime import date
from pathlib import Path

from generator.generate import Rates, generate_all


def _header_drift(value: str) -> tuple[str, str, str]:
    parts = value.split(":", 2)
    if len(parts) != 3:
        raise argparse.ArgumentTypeError(
            "--header-drift 格式須為 table:field_en:new_name_zh"
        )
    return tuple(parts)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="generator", description="合成資料產生器(T0.5)"
    )
    parser.add_argument("--out", type=Path, default=Path("generator/out"))
    parser.add_argument("--tenants", nargs="+", default=["alpha", "beta"])
    parser.add_argument("--rows", type=int, default=500, help="每租戶每表基底列數")
    parser.add_argument("--batches", type=int, default=5, help="日批次數")
    parser.add_argument(
        "--start-date", type=date.fromisoformat, default=date(2026, 1, 1)
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--missing-rate", type=float, default=0.05)
    parser.add_argument("--duplicate-rate", type=float, default=0.05)
    parser.add_argument("--drift-rate", type=float, default=0.05)
    parser.add_argument("--late-rate", type=float, default=0.05)
    parser.add_argument(
        "--header-drift",
        type=_header_drift,
        default=None,
        help="單欄表頭改名,模擬欄位名稱漂移,格式 table:field_en:new_name_zh(T1.3 驗票用)",
    )
    args = parser.parse_args(argv)

    written = generate_all(
        out_dir=args.out,
        tenants=args.tenants,
        rows=args.rows,
        batches=args.batches,
        start_date=args.start_date,
        seed=args.seed,
        rates=Rates(
            missing=args.missing_rate,
            duplicate=args.duplicate_rate,
            drift=args.drift_rate,
            late=args.late_rate,
        ),
        header_drift=args.header_drift,
    )
    print(f"寫出 {len(written)} 個檔案 → {args.out}")
