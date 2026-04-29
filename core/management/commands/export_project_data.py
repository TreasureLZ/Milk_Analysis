# -*- coding: utf-8 -*-
"""
导出项目数据库数据到 CSV / Excel。

用法：
  python manage.py export_project_data
  python manage.py export_project_data --outdir exports
  python manage.py export_project_data --format csv
  python manage.py export_project_data --format xlsx
  python manage.py export_project_data --format both
  python manage.py export_project_data --tables core_product core_review
"""

from __future__ import annotations

import csv
import os
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


_SAFE_SHEET_NAME_RE = re.compile(r"[^0-9A-Za-z_\-\u4e00-\u9fff]+")


@dataclass(frozen=True)
class TableInfo:
    name: str
    columns: List[str]
    row_count: int


def _get_sqlite_db_path() -> Path:
    db = settings.DATABASES.get("default", {})
    engine = (db.get("ENGINE") or "").lower()
    if "sqlite3" not in engine:
        raise CommandError(f"当前数据库引擎不是 SQLite：{db.get('ENGINE')}")
    name = db.get("NAME")
    if not name:
        raise CommandError("未配置 SQLite 数据库路径（DATABASES['default']['NAME']）")
    return Path(str(name)).resolve()


def _connect(db_path: Path) -> sqlite3.Connection:
    if not db_path.exists():
        raise CommandError(f"数据库文件不存在：{db_path}")
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def _list_tables(conn: sqlite3.Connection) -> List[str]:
    # 排除 SQLite 内部表
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ).fetchall()
    return [r["name"] for r in rows]


def _get_columns(conn: sqlite3.Connection, table: str) -> List[str]:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return [r["name"] for r in rows]


def _get_row_count(conn: sqlite3.Connection, table: str) -> int:
    row = conn.execute(f"SELECT COUNT(1) AS c FROM {table}").fetchone()
    return int(row["c"])


def _fetch_all_rows(conn: sqlite3.Connection, table: str, columns: Sequence[str]) -> List[sqlite3.Row]:
    col_sql = ", ".join([f'"{c}"' for c in columns]) if columns else "*"
    return conn.execute(f"SELECT {col_sql} FROM {table}").fetchall()


def _ensure_outdir(outdir: Path) -> None:
    outdir.mkdir(parents=True, exist_ok=True)


def _write_csv(path: Path, columns: Sequence[str], rows: Sequence[sqlite3.Row]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(list(columns))
        for r in rows:
            w.writerow([r[c] for c in columns])


def _safe_sheet_name(table: str) -> str:
    # Excel sheet name: max 31 chars; cannot contain : \ / ? * [ ]
    cleaned = _SAFE_SHEET_NAME_RE.sub("_", table).strip("_")
    if not cleaned:
        cleaned = "sheet"
    cleaned = cleaned.replace(":", "_").replace("\\", "_").replace("/", "_").replace("?", "_")
    cleaned = cleaned.replace("*", "_").replace("[", "_").replace("]", "_")
    return cleaned[:31]


def _write_excel(path: Path, tables: Sequence[Tuple[str, Sequence[str], Sequence[sqlite3.Row]]]) -> None:
    try:
        import pandas as pd  # type: ignore
    except Exception as e:  # pragma: no cover
        raise CommandError(f"未安装 pandas，无法导出 Excel：{e}")

    try:
        import openpyxl  # noqa: F401
    except Exception as e:
        raise CommandError(
            f"导出 xlsx 需要安装 openpyxl。请在虚拟环境中执行：pip install openpyxl。原始错误：{e}"
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(str(path), engine="openpyxl") as writer:
        used = set()
        for table, columns, rows in tables:
            data = [{c: r[c] for c in columns} for r in rows]
            df = pd.DataFrame(data, columns=list(columns))
            sheet = _safe_sheet_name(table)
            # 处理不同表清洗后重名的情况
            base = sheet
            i = 2
            while sheet in used:
                suffix = f"_{i}"
                sheet = (base[: (31 - len(suffix))] + suffix)[:31]
                i += 1
            used.add(sheet)
            df.to_excel(writer, sheet_name=sheet, index=False)


class Command(BaseCommand):
    help = "导出 SQLite 数据库中的所有数据表到 CSV/Excel，便于直观看到项目数据"

    def add_arguments(self, parser):
        parser.add_argument(
            "--outdir",
            type=str,
            default="exports",
            help="导出目录（相对 milk_analysis 根目录），默认 exports",
        )
        parser.add_argument(
            "--format",
            type=str,
            choices=["csv", "xlsx", "both"],
            default="csv",
            help="导出格式：csv / xlsx / both（默认 csv）",
        )
        parser.add_argument(
            "--tables",
            nargs="*",
            default=None,
            help="只导出指定表名（空格分隔）。不传则导出全部表",
        )

    def handle(self, *args, **options):
        db_path = _get_sqlite_db_path()
        project_root = Path(settings.BASE_DIR).resolve()
        outdir = (project_root / str(options["outdir"])).resolve()

        requested_tables: Optional[Sequence[str]] = options.get("tables")
        export_format: str = options["format"]

        _ensure_outdir(outdir)
        self.stdout.write(f"数据库：{db_path}")
        self.stdout.write(f"导出目录：{outdir}")

        with _connect(db_path) as conn:
            all_tables = _list_tables(conn)
            if requested_tables:
                missing = [t for t in requested_tables if t not in all_tables]
                if missing:
                    raise CommandError(f"指定的表不存在：{missing}\n可用表：{all_tables}")
                tables = list(requested_tables)
            else:
                tables = all_tables

            infos: List[TableInfo] = []
            excel_payload: List[Tuple[str, Sequence[str], Sequence[sqlite3.Row]]] = []

            for t in tables:
                cols = _get_columns(conn, t)
                cnt = _get_row_count(conn, t)
                infos.append(TableInfo(name=t, columns=cols, row_count=cnt))

                rows = _fetch_all_rows(conn, t, cols)
                if export_format in ("csv", "both"):
                    _write_csv(outdir / f"{t}.csv", cols, rows)

                if export_format in ("xlsx", "both"):
                    excel_payload.append((t, cols, rows))

            # summary
            summary_path = outdir / "tables_summary.csv"
            with summary_path.open("w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f)
                w.writerow(["table", "row_count", "columns"])
                for info in infos:
                    w.writerow([info.name, info.row_count, ", ".join(info.columns)])

            if export_format in ("xlsx", "both"):
                _write_excel(outdir / "all_tables.xlsx", excel_payload)

        self.stdout.write(self.style.SUCCESS("导出完成。"))

