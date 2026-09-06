from __future__ import annotations

import re
import sqlite3
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "run.sqlite"
IST = ZoneInfo("Asia/Kolkata")

STATUSES = ("pending", "success")
TSHIRTS = ("XS", "S", "M", "L", "XL", "XXL", "3XL")
DISTANCES = ("5K", "10K")


def now() -> str:
    return datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")


def clean(value, max_len: int = 300) -> str:
    text = re.sub(r"[\r\n]+", " ", str(value or "")).strip()
    text = re.sub(r"<[^>]+>", "", text)
    return text[:max_len]


def norm_phone(raw: str) -> str:
    digits = re.sub(r"\D+", "", raw or "")
    if len(digits) == 10:
        digits = "91" + digits
    if len(digits) == 11 and digits.startswith("0"):
        digits = "91" + digits[1:]
    return digits


def connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            phone_norm TEXT NOT NULL,
            tshirt TEXT NOT NULL,
            distance TEXT NOT NULL,
            screenshot TEXT DEFAULT '',
            status TEXT DEFAULT 'pending',
            email_sent_at TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_run_status ON registrations(status)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_run_token ON registrations(token)")
    conn.commit()
    return conn


def create(data: dict) -> dict:
    name = clean(data.get("name"), 120)
    email = clean(data.get("email"), 160).lower()
    phone = clean(data.get("phone"), 30)
    phone_norm = norm_phone(phone)
    tshirt = clean(data.get("tshirt"), 8).upper()
    distance = clean(data.get("distance"), 8).upper()
    if not name or "@" not in email or len(phone_norm) < 12:
        raise ValueError("Name, a valid email, and a 10-digit mobile number are required.")
    if tshirt not in TSHIRTS:
        raise ValueError("Choose a T-shirt size.")
    if distance not in DISTANCES:
        raise ValueError("Choose 5K or 10K.")
    stamp = now()
    conn = connect()
    conn.execute(
        """
        INSERT INTO registrations (
            token, name, email, phone, phone_norm, tshirt, distance,
            status, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)
        """,
        (data["token"], name, email, phone, phone_norm, tshirt, distance, stamp, stamp),
    )
    row_id = int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])
    conn.commit()
    row = conn.execute("SELECT * FROM registrations WHERE id = ?", (row_id,)).fetchone()
    conn.close()
    return dict(row)


def get_by_token(token: str) -> dict | None:
    conn = connect()
    row = conn.execute("SELECT * FROM registrations WHERE token = ?", (token,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get(reg_id: int) -> dict | None:
    conn = connect()
    row = conn.execute("SELECT * FROM registrations WHERE id = ?", (reg_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def save_screenshot(token: str, filename: str) -> dict:
    row = get_by_token(token)
    if not row:
        raise ValueError("Registration not found.")
    conn = connect()
    conn.execute(
        "UPDATE registrations SET screenshot = ?, updated_at = ? WHERE token = ?",
        (filename, now(), token),
    )
    conn.commit()
    updated = conn.execute("SELECT * FROM registrations WHERE token = ?", (token,)).fetchone()
    conn.close()
    return dict(updated)


def set_status(reg_id: int, status: str) -> dict:
    if status not in STATUSES:
        raise ValueError("Invalid status")
    row = get(reg_id)
    if not row:
        raise ValueError("Registration not found.")
    conn = connect()
    conn.execute(
        "UPDATE registrations SET status = ?, updated_at = ? WHERE id = ?",
        (status, now(), reg_id),
    )
    conn.commit()
    updated = conn.execute("SELECT * FROM registrations WHERE id = ?", (reg_id,)).fetchone()
    conn.close()
    return dict(updated)


def mark_email_sent(reg_id: int) -> None:
    conn = connect()
    conn.execute(
        "UPDATE registrations SET email_sent_at = ?, updated_at = ? WHERE id = ?",
        (now(), now(), reg_id),
    )
    conn.commit()
    conn.close()


def list_regs(status: str = "", q: str = "") -> list[dict]:
    where = ["1=1"]
    params: list = []
    if status in STATUSES:
        where.append("status = ?")
        params.append(status)
    if q:
        where.append("(name LIKE ? OR email LIKE ? OR phone LIKE ? OR phone_norm LIKE ?)")
        like = f"%{q}%"
        params.extend([like, like, like, like])
    conn = connect()
    rows = conn.execute(
        f"SELECT * FROM registrations WHERE {' AND '.join(where)} ORDER BY id DESC LIMIT 500",
        params,
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def stats() -> dict:
    conn = connect()
    today = datetime.now(IST).strftime("%Y-%m-%d")
    result = {
        "total": conn.execute("SELECT COUNT(*) FROM registrations").fetchone()[0],
        "pending": conn.execute("SELECT COUNT(*) FROM registrations WHERE status = 'pending'").fetchone()[0],
        "success": conn.execute("SELECT COUNT(*) FROM registrations WHERE status = 'success'").fetchone()[0],
        "today": conn.execute(
            "SELECT COUNT(*) FROM registrations WHERE created_at LIKE ?", (f"{today}%",)
        ).fetchone()[0],
    }
    conn.close()
    return result


def format_when(value: str) -> str:
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S").strftime("%d %b, %I:%M %p")
    except ValueError:
        return value or "—"
