from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import List, Dict, Any

try:
    from email_validator import validate_email, EmailNotValidError  # type: ignore

    _EMAIL_LIB_OK = True
except Exception:  # pragma: no cover
    _EMAIL_LIB_OK = False
    EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

DATETIME_FMT = "%Y-%m-%d %H:%M:%S"

SCHEMA = ["number", "datetime", "email", "text1", "text2", "text3", "text4"]


@dataclass
class RowError:
    line: int
    column: int
    field: str
    message: str
    value: str

    def as_dict(self) -> Dict[str, Any]:
        return {
            "line": self.line,
            "column": self.column,
            "field": self.field,
            "message": self.message,
            "value": self.value,
        }


@dataclass
class ValidationResult:
    ok: bool
    rows_total: int
    rows_valid: int
    rows_invalid: int
    errors: List[RowError]
    skipped_header: bool

    def as_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "schema": SCHEMA,
            "rows_total": self.rows_total,
            "rows_valid": self.rows_valid,
            "rows_invalid": self.rows_invalid,
            "skipped_header": self.skipped_header,
            "errors": [e.as_dict() for e in self.errors],
        }


def _is_number(s: str) -> bool:
    try:
        Decimal(s)
        return True
    except (InvalidOperation, ValueError):
        return False


def _is_datetime(s: str) -> bool:
    try:
        datetime.strptime(s, DATETIME_FMT)
        return True
    except ValueError:
        return False


def _is_email(s: str) -> bool:
    if _EMAIL_LIB_OK:
        try:
            validate_email(s, check_deliverability=False)
            return True
        except EmailNotValidError:
            return False
    else:
        return bool(EMAIL_REGEX.match(s))


def validate_tsv(text: str) -> Dict[str, Any]:
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    reader = csv.reader(text.splitlines(), delimiter="\t")
    errors: List[RowError] = []
    rows_total = 0
    rows_valid = 0
    skipped_header = False

    rows = list(reader)
    if not rows:
        return ValidationResult(
            ok=False,
            rows_total=0,
            rows_valid=0,
            rows_invalid=0,
            errors=[RowError(1, 1, "file", "Файл пуст", "").as_dict()],  # type: ignore
            skipped_header=False,
        ).as_dict()

    first = rows[0]
    if first and not _is_number(first[0]):
        skipped_header = True
        data_rows = rows[1:]
        first_data_line_no = 2
    else:
        data_rows = rows
        first_data_line_no = 1

    for idx, row in enumerate(data_rows, start=first_data_line_no):
        if not row or (len(row) == 1 and row[0].strip() == ""):
            continue

        rows_total += 1

        if not _is_number(row[0].strip()):
            errors.append(RowError(idx, 1, "number", "Неверное число", row[0]))
            continue

        if not _is_datetime(row[1].strip()):
            errors.append(RowError(idx, 2, "datetime", f"Ожидался формат {DATETIME_FMT}", row[1]))
            continue

        if not _is_email(row[2].strip()):
            errors.append(RowError(idx, 3, "email", "Неверный адрес электронной почты", row[2]))
            continue

        rows_valid += 1

    rows_invalid = rows_total - rows_valid

    return ValidationResult(
        ok=rows_invalid == 0,
        rows_total=rows_total,
        rows_valid=rows_valid,
        rows_invalid=rows_invalid,
        errors=errors,
        skipped_header=skipped_header,
    ).as_dict()
