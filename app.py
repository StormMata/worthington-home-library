#!/usr/bin/env python3
"""Shelf Index: a dependency-free, local-first physical media catalogue."""

from __future__ import annotations

import csv
import io
import json
import mimetypes
import os
import re
import shutil
import sqlite3
import sys
import tempfile
import time
import webbrowser
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, quote, unquote, urlencode, urlparse
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent
STATIC_DIR = ROOT / "static"
PUBLIC_SITE_DIR = ROOT / "public_site"
PAGES_DIR = ROOT / "docs"
DATA_DIR = ROOT / "data"
DIGITAL_LIBRARY_DIR = ROOT / "digital_library"
DB_PATH = Path(os.environ.get("SHELF_INDEX_DB", DATA_DIR / "catalogue.sqlite3"))
HOST = os.environ.get("SHELF_INDEX_HOST", "127.0.0.1")
PORT = int(os.environ.get("SHELF_INDEX_PORT", "8765"))


class ClosingConnection(sqlite3.Connection):
    """A SQLite connection whose context manager also closes the file handle."""

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            return super().__exit__(exc_type, exc_value, traceback)
        finally:
            self.close()


SCHEMA = """
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    subtitle TEXT,
    media_category TEXT NOT NULL DEFAULT 'Book',
    item_type TEXT NOT NULL DEFAULT 'Single work',
    publication_date TEXT,
    publisher TEXT,
    edition TEXT,
    identifier TEXT,
    language TEXT,
    description TEXT,
    set_name TEXT,
    volume_label TEXT,
    volume_number REAL,
    stack TEXT,
    shelf_row TEXT,
    shelf_position TEXT,
    notes TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS works (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    work_type TEXT,
    publication_date TEXT,
    language TEXT,
    notes TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS item_contents (
    item_id INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    work_id INTEGER NOT NULL REFERENCES works(id) ON DELETE CASCADE,
    sequence_no INTEGER,
    page_start TEXT,
    page_end TEXT,
    PRIMARY KEY (item_id, work_id)
);

CREATE TABLE IF NOT EXISTS digital_files (
    id INTEGER PRIMARY KEY,
    item_id INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    label TEXT,
    relative_path TEXT NOT NULL,
    notes TEXT,
    sequence_no INTEGER,
    UNIQUE (item_id, relative_path)
);

CREATE TABLE IF NOT EXISTS people (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL COLLATE NOCASE UNIQUE
);

CREATE TABLE IF NOT EXISTS credits (
    id INTEGER PRIMARY KEY,
    item_id INTEGER REFERENCES items(id) ON DELETE CASCADE,
    work_id INTEGER REFERENCES works(id) ON DELETE CASCADE,
    person_id INTEGER NOT NULL REFERENCES people(id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    CHECK ((item_id IS NOT NULL) != (work_id IS NOT NULL))
);

CREATE INDEX IF NOT EXISTS idx_items_location ON items(stack, shelf_row);
CREATE INDEX IF NOT EXISTS idx_items_category ON items(media_category);
CREATE INDEX IF NOT EXISTS idx_items_set ON items(set_name, volume_number);
CREATE INDEX IF NOT EXISTS idx_contents_item ON item_contents(item_id, sequence_no);
CREATE INDEX IF NOT EXISTS idx_digital_files_item ON digital_files(item_id, sequence_no);
CREATE INDEX IF NOT EXISTS idx_credits_item ON credits(item_id);
CREATE INDEX IF NOT EXISTS idx_credits_work ON credits(work_id);

CREATE VIRTUAL TABLE IF NOT EXISTS catalog_fts USING fts5(
    item_id UNINDEXED,
    searchable,
    tokenize = 'unicode61 remove_diacritics 2'
);

CREATE TABLE IF NOT EXISTS isbn_cache (
    isbn TEXT PRIMARY KEY,
    response_json TEXT NOT NULL,
    fetched_at TEXT NOT NULL
);
"""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH, timeout=10, factory=ClosingConnection)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    return db


def init_db() -> None:
    DIGITAL_LIBRARY_DIR.mkdir(parents=True, exist_ok=True)
    with connect() as db:
        db.executescript(SCHEMA)


def clean_text(value):
    if value is None:
        return None
    value = str(value).strip()
    return value or None


def clean_number(value):
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def normalize_digital_path(value: str) -> str:
    """Return a safe path relative to the project's digital library."""
    path = (clean_text(value) or "").replace("\\", "/")
    if path.startswith("/") or re.match(r"^[A-Za-z]:/", path):
        raise ValueError("Digital file paths must stay inside digital_library")
    while path.startswith("./"):
        path = path[2:]
    path = re.sub(r"/+", "/", path)
    if not path or any(part in ("", ".", "..") for part in path.split("/")):
        raise ValueError("Digital file paths must stay inside digital_library")
    return path


def digital_files_value(value) -> list[dict]:
    if not value:
        return []
    if not isinstance(value, list):
        raise ValueError("Digital files must be a list")
    result = []
    seen = set()
    for entry in value:
        if not isinstance(entry, dict) or not clean_text(entry.get("relative_path")):
            continue
        relative_path = normalize_digital_path(entry["relative_path"])
        if relative_path in seen:
            continue
        seen.add(relative_path)
        result.append({
            "relative_path": relative_path,
            "label": clean_text(entry.get("label")),
            "notes": clean_text(entry.get("notes")),
        })
    return result


def normalize_isbn(value: str) -> str:
    """Return a validated ISBN-10 or ISBN-13 without separators."""
    isbn = re.sub(r"[^0-9Xx]", "", value or "").upper()
    if len(isbn) == 10:
        if not re.fullmatch(r"\d{9}[\dX]", isbn):
            raise ValueError("Enter a valid ISBN-10 or ISBN-13")
        total = sum((10 - index) * (10 if char == "X" else int(char)) for index, char in enumerate(isbn))
        if total % 11:
            raise ValueError("This ISBN-10 has an invalid check digit")
        return isbn
    if len(isbn) == 13:
        if not isbn.isdigit():
            raise ValueError("Enter a valid ISBN-10 or ISBN-13")
        total = sum(int(char) * (1 if index % 2 == 0 else 3) for index, char in enumerate(isbn[:12]))
        expected = (10 - total % 10) % 10
        if expected != int(isbn[-1]):
            raise ValueError("This ISBN-13 has an invalid check digit")
        return isbn
    raise ValueError("Enter a valid ISBN-10 or ISBN-13")


def _first_name(entries) -> str | None:
    for entry in entries or []:
        if isinstance(entry, dict) and clean_text(entry.get("name")):
            return clean_text(entry["name"])
        if clean_text(entry):
            return clean_text(entry)
    return None


def transform_open_library(isbn: str, book: dict) -> dict:
    languages = []
    language_names = {"eng": "English", "fre": "French", "ger": "German", "spa": "Spanish", "ita": "Italian", "lat": "Latin"}
    for language in book.get("languages") or []:
        value = language.get("key") if isinstance(language, dict) else language
        code = str(value or "").rsplit("/", 1)[-1]
        if code:
            languages.append(language_names.get(code, code))
    description = book.get("description")
    if isinstance(description, dict):
        description = description.get("value")
    subjects = []
    for subject in (book.get("subjects") or book.get("subject") or [])[:12]:
        name = clean_text(subject.get("name")) if isinstance(subject, dict) else clean_text(subject)
        if name:
            subjects.append(name)
    fields = {
        "title": clean_text(book.get("title")),
        "subtitle": clean_text(book.get("subtitle")),
        "publication_date": clean_text(book.get("publish_date")),
        "publisher": _first_name(book.get("publishers")),
        "identifier": isbn,
        "language": ", ".join(dict.fromkeys(languages)) or None,
        "description": clean_text(description),
    }
    authors = [
        {"name": clean_text(author.get("name")), "role": "Author"}
        for author in book.get("authors") or []
        if isinstance(author, dict) and clean_text(author.get("name"))
    ]
    source_url = clean_text(book.get("url")) or f"https://openlibrary.org/isbn/{isbn}"
    return {
        "isbn": isbn,
        "source": "Open Library",
        "source_url": source_url,
        "fields": {key: value for key, value in fields.items() if value},
        "contributors": authors,
        "additional": {
            "Number of pages": book.get("number_of_pages") or book.get("number_of_pages_median"),
            "Physical format": clean_text(book.get("physical_format")),
            "Open Library subjects": ", ".join(subjects) or None,
        },
    }


def _open_library_json(url: str, missing_ok: bool = False) -> dict | None:
    request = Request(url, headers={
        "Accept": "application/json",
        "User-Agent": "WorthingtonHomeLibrary/1.0 (local personal catalogue)",
    })
    try:
        with urlopen(request, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        if exc.code == 404 and missing_ok:
            return None
        raise ConnectionError(f"Open Library returned an error ({exc.code})") from exc
    except (URLError, TimeoutError) as exc:
        raise ConnectionError("Could not reach Open Library. Check your internet connection and try again.") from exc
    return payload


def fetch_open_library(isbn: str) -> dict:
    # The edition endpoint supplies ISBN-specific publication data. The Search
    # API then supplies author names, which edition records usually store only
    # as opaque author keys.
    edition = _open_library_json(f"https://openlibrary.org/isbn/{isbn}.json", missing_ok=True)
    if edition:
        time.sleep(1.05)  # Respect Open Library's default one-request-per-second limit.
    query = urlencode({
        "isbn": isbn,
        "fields": "key,title,subtitle,author_name,publisher,publish_date,isbn,language,number_of_pages_median,subject",
        "limit": 1,
    })
    search = _open_library_json(f"https://openlibrary.org/search.json?{query}") or {}
    document = (search.get("docs") or [None])[0]
    if not edition and not document:
        raise LookupError("Open Library has no record for this ISBN")
    if edition:
        book = dict(edition)
        if document and document.get("author_name"):
            book["authors"] = [{"name": name} for name in document["author_name"]]
        book["url"] = f"https://openlibrary.org{edition.get('key', '')}" if edition.get("key") else None
    else:
        book = dict(document)
        book["authors"] = [{"name": name} for name in document.get("author_name") or []]
        publishers = document.get("publisher") or []
        dates = document.get("publish_date") or []
        book["publishers"] = publishers[:1]
        book["publish_date"] = dates[0] if dates else None
        book["url"] = f"https://openlibrary.org{document.get('key', '')}" if document.get("key") else None
    return transform_open_library(isbn, book)


def lookup_isbn(value: str, refresh: bool = False) -> dict:
    isbn = normalize_isbn(value)
    with connect() as db:
        cached = db.execute("SELECT response_json, fetched_at FROM isbn_cache WHERE isbn=?", (isbn,)).fetchone()
        if cached and not refresh:
            result = json.loads(cached["response_json"])
            result.update({"cached": True, "fetched_at": cached["fetched_at"]})
            return result
    result = fetch_open_library(isbn)
    fetched_at = utc_now()
    with connect() as db:
        db.execute(
            "INSERT INTO isbn_cache(isbn, response_json, fetched_at) VALUES (?, ?, ?) "
            "ON CONFLICT(isbn) DO UPDATE SET response_json=excluded.response_json, fetched_at=excluded.fetched_at",
            (isbn, json.dumps(result, ensure_ascii=False), fetched_at),
        )
    return {**result, "cached": False, "fetched_at": fetched_at}


def metadata_value(value) -> dict:
    if not value:
        return {}
    if isinstance(value, dict):
        return {str(k): v for k, v in value.items() if str(k).strip()}
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


def contributors_value(value) -> list[dict]:
    if not value:
        return []
    if isinstance(value, str):
        # CSV-friendly: "Author: Name; Editor: Name"
        result = []
        for part in value.split(";"):
            part = part.strip()
            if not part:
                continue
            role, sep, name = part.partition(":")
            result.append({"role": role.strip() if sep else "Contributor", "name": (name if sep else role).strip()})
        return result
    return [
        {"name": clean_text(entry.get("name")), "role": clean_text(entry.get("role")) or "Contributor"}
        for entry in value
        if isinstance(entry, dict) and clean_text(entry.get("name"))
    ]


def set_credits(db: sqlite3.Connection, *, item_id=None, work_id=None, contributors=None) -> None:
    if item_id is not None:
        db.execute("DELETE FROM credits WHERE item_id = ?", (item_id,))
    else:
        db.execute("DELETE FROM credits WHERE work_id = ?", (work_id,))
    for contributor in contributors_value(contributors):
        db.execute("INSERT INTO people(name) VALUES (?) ON CONFLICT(name) DO NOTHING", (contributor["name"],))
        person_id = db.execute("SELECT id FROM people WHERE name = ? COLLATE NOCASE", (contributor["name"],)).fetchone()[0]
        db.execute(
            "INSERT INTO credits(item_id, work_id, person_id, role) VALUES (?, ?, ?, ?)",
            (item_id, work_id, person_id, contributor["role"]),
        )


def rebuild_search(db: sqlite3.Connection, item_id: int) -> None:
    db.execute("DELETE FROM catalog_fts WHERE item_id = ?", (item_id,))
    item = db.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    if not item:
        return
    parts = [str(value) for value in dict(item).values() if value is not None]
    rows = db.execute(
        """
        SELECT w.*, ic.page_start, ic.page_end,
               group_concat(p.name || ' ' || c.role, ' ') AS contributor_text
        FROM item_contents ic
        JOIN works w ON w.id = ic.work_id
        LEFT JOIN credits c ON c.work_id = w.id
        LEFT JOIN people p ON p.id = c.person_id
        WHERE ic.item_id = ?
        GROUP BY w.id
        """,
        (item_id,),
    ).fetchall()
    item_people = db.execute(
        "SELECT group_concat(p.name || ' ' || c.role, ' ') FROM credits c JOIN people p ON p.id=c.person_id WHERE c.item_id=?",
        (item_id,),
    ).fetchone()[0]
    if item_people:
        parts.append(item_people)
    for row in rows:
        parts.extend(str(value) for value in dict(row).values() if value is not None)
    for row in db.execute("SELECT label, relative_path, notes FROM digital_files WHERE item_id=?", (item_id,)):
        parts.extend(str(value) for value in row if value is not None)
    db.execute("INSERT INTO catalog_fts(item_id, searchable) VALUES (?, ?)", (item_id, " ".join(parts)))


def item_summary(row: sqlite3.Row) -> dict:
    result = dict(row)
    result["location"] = ", ".join(
        label for label in [
            f"Stack {result['stack']}" if result.get("stack") else None,
            f"Row {result['shelf_row']}" if result.get("shelf_row") else None,
            result.get("shelf_position"),
        ] if label
    )
    result["volume_display"] = result.get("volume_label") or (
        f"Volume {result['volume_number']:g}" if result.get("volume_number") is not None else None
    )
    return result


def get_item(db: sqlite3.Connection, item_id: int) -> dict | None:
    row = db.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    if not row:
        return None
    item = item_summary(row)
    item["metadata"] = json.loads(item.pop("metadata_json") or "{}")
    item["contributors"] = [dict(r) for r in db.execute(
        "SELECT p.name, c.role FROM credits c JOIN people p ON p.id=c.person_id WHERE c.item_id=? ORDER BY c.id", (item_id,)
    )]
    item["digital_files"] = []
    for row in db.execute(
        "SELECT label, relative_path, notes, sequence_no FROM digital_files WHERE item_id=? ORDER BY COALESCE(sequence_no, 999999), id",
        (item_id,),
    ):
        digital_file = dict(row)
        digital_file["exists"] = (DIGITAL_LIBRARY_DIR / digital_file["relative_path"]).is_file()
        digital_file["url"] = "/digital/" + quote(digital_file["relative_path"], safe="/")
        item["digital_files"].append(digital_file)
    contents = []
    for work in db.execute(
        """
        SELECT w.*, ic.sequence_no, ic.page_start, ic.page_end
        FROM item_contents ic JOIN works w ON w.id=ic.work_id
        WHERE ic.item_id=? ORDER BY COALESCE(ic.sequence_no, 999999), w.id
        """, (item_id,)
    ):
        content = dict(work)
        content["metadata"] = json.loads(content.pop("metadata_json") or "{}")
        content["contributors"] = [dict(r) for r in db.execute(
            "SELECT p.name, c.role FROM credits c JOIN people p ON p.id=c.person_id WHERE c.work_id=? ORDER BY c.id", (work["id"],)
        )]
        contents.append(content)
    item["contents"] = contents
    return item


ITEM_FIELDS = [
    "title", "subtitle", "media_category", "item_type", "publication_date", "publisher", "edition",
    "identifier", "language", "description", "set_name", "volume_label", "volume_number", "stack",
    "shelf_row", "shelf_position", "notes",
]


def save_item(payload: dict, item_id: int | None = None) -> int:
    title = clean_text(payload.get("title"))
    if not title:
        raise ValueError("Title is required")
    values = {field: clean_text(payload.get(field)) for field in ITEM_FIELDS}
    values["title"] = title
    values["media_category"] = values["media_category"] or "Book"
    values["item_type"] = values["item_type"] or "Single work"
    values["volume_number"] = clean_number(payload.get("volume_number"))
    values["metadata_json"] = json.dumps(metadata_value(payload.get("metadata")), ensure_ascii=False)
    now = utc_now()
    with connect() as db:
        if item_id is None:
            columns = ITEM_FIELDS + ["metadata_json", "created_at", "updated_at"]
            params = [values.get(column) for column in ITEM_FIELDS] + [values["metadata_json"], now, now]
            markers = ", ".join("?" for _ in columns)
            item_id = db.execute(
                f"INSERT INTO items({', '.join(columns)}) VALUES ({markers})", params
            ).lastrowid
        else:
            if not db.execute("SELECT 1 FROM items WHERE id=?", (item_id,)).fetchone():
                raise LookupError("Item not found")
            assignments = ", ".join(f"{field}=?" for field in ITEM_FIELDS + ["metadata_json"])
            params = [values.get(column) for column in ITEM_FIELDS] + [values["metadata_json"], now, item_id]
            db.execute(f"UPDATE items SET {assignments}, updated_at=? WHERE id=?", params)
            old_work_ids = [r[0] for r in db.execute("SELECT work_id FROM item_contents WHERE item_id=?", (item_id,))]
            db.execute("DELETE FROM item_contents WHERE item_id=?", (item_id,))
            for work_id in old_work_ids:
                db.execute("DELETE FROM works WHERE id=?", (work_id,))
        set_credits(db, item_id=item_id, contributors=payload.get("contributors"))
        db.execute("DELETE FROM digital_files WHERE item_id=?", (item_id,))
        for index, digital_file in enumerate(digital_files_value(payload.get("digital_files")), start=1):
            db.execute(
                "INSERT INTO digital_files(item_id, label, relative_path, notes, sequence_no) VALUES (?, ?, ?, ?, ?)",
                (item_id, digital_file["label"], digital_file["relative_path"], digital_file["notes"], index),
            )
        for index, content in enumerate(payload.get("contents") or [], start=1):
            content_title = clean_text(content.get("title"))
            if not content_title:
                continue
            work_id = db.execute(
                "INSERT INTO works(title, work_type, publication_date, language, notes, metadata_json) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    content_title, clean_text(content.get("work_type")), clean_text(content.get("publication_date")),
                    clean_text(content.get("language")), clean_text(content.get("notes")),
                    json.dumps(metadata_value(content.get("metadata")), ensure_ascii=False),
                ),
            ).lastrowid
            db.execute(
                "INSERT INTO item_contents(item_id, work_id, sequence_no, page_start, page_end) VALUES (?, ?, ?, ?, ?)",
                (item_id, work_id, content.get("sequence_no") or index, clean_text(content.get("page_start")), clean_text(content.get("page_end"))),
            )
            set_credits(db, work_id=work_id, contributors=content.get("contributors"))
        rebuild_search(db, item_id)
    return item_id


def search_items(query: str = "", category: str = "", stack: str = "", row: str = "") -> list[dict]:
    clauses, params = [], []
    joins = ""
    tokens = re.findall(r"[\w'-]+", query, flags=re.UNICODE)
    if tokens:
        joins = "JOIN catalog_fts f ON f.item_id = i.id"
        clauses.append("catalog_fts MATCH ?")
        params.append(" AND ".join('"' + token.replace('"', '""') + '"*' for token in tokens))
    if category:
        clauses.append("i.media_category = ?")
        params.append(category)
    if stack:
        clauses.append("i.stack = ?")
        params.append(stack)
    if row:
        clauses.append("i.shelf_row = ?")
        params.append(row)
    where = "WHERE " + " AND ".join(clauses) if clauses else ""
    rank = ", bm25(catalog_fts) AS rank" if tokens else ""
    order = "rank, i.title COLLATE NOCASE" if tokens else "i.updated_at DESC, i.title COLLATE NOCASE"
    sql = f"""
        SELECT i.*{rank},
          (SELECT group_concat(p.name, ', ') FROM credits c JOIN people p ON p.id=c.person_id WHERE c.item_id=i.id) contributors,
          (SELECT count(*) FROM item_contents ic WHERE ic.item_id=i.id) content_count,
          (SELECT count(*) FROM digital_files df WHERE df.item_id=i.id) digital_file_count
        FROM items i {joins} {where} ORDER BY {order} LIMIT 250
    """
    with connect() as db:
        results = [item_summary(row) for row in db.execute(sql, params)]
        if tokens:
            folded_tokens = [token.casefold() for token in tokens]
            for result in results:
                matches = []
                content_rows = db.execute(
                    """
                    SELECT w.title, w.work_type, ic.page_start, ic.page_end,
                           group_concat(p.name, ', ') AS contributors
                    FROM item_contents ic
                    JOIN works w ON w.id=ic.work_id
                    LEFT JOIN credits c ON c.work_id=w.id
                    LEFT JOIN people p ON p.id=c.person_id
                    WHERE ic.item_id=?
                    GROUP BY w.id
                    ORDER BY COALESCE(ic.sequence_no, 999999), w.id
                    """,
                    (result["id"],),
                )
                for content in content_rows:
                    candidate = dict(content)
                    haystack = " ".join(str(value) for value in candidate.values() if value).casefold()
                    if all(token in haystack for token in folded_tokens):
                        matches.append(candidate)
                result["matched_contents"] = matches[:3]
        return results


def options() -> dict:
    with connect() as db:
        def distinct(column):
            return [r[0] for r in db.execute(f"SELECT DISTINCT {column} FROM items WHERE {column} IS NOT NULL AND {column} != '' ORDER BY {column} COLLATE NOCASE")]
        return {
            "categories": distinct("media_category"),
            "stacks": distinct("stack"),
            "rows": distinct("shelf_row"),
            "item_types": distinct("item_type"),
            "counts": {
                "items": db.execute("SELECT count(*) FROM items").fetchone()[0],
                "contents": db.execute("SELECT count(*) FROM works").fetchone()[0],
            },
        }


def parse_import(payload: dict) -> list[dict]:
    fmt = (payload.get("format") or "json").lower()
    content = payload.get("content") or ""
    if fmt == "json":
        parsed = json.loads(content)
        records = parsed.get("items", []) if isinstance(parsed, dict) else parsed
        if not isinstance(records, list):
            raise ValueError("JSON must be an array of items or an object with an items array")
        return records
    if fmt == "csv":
        rows = list(csv.DictReader(io.StringIO(content.lstrip("\ufeff"))))
        grouped = {}
        for index, row in enumerate(rows, start=1):
            key = clean_text(row.get("record_key")) or f"row-{index}"
            if key not in grouped:
                grouped[key] = {
                    field: row.get(field) for field in ITEM_FIELDS if field in row
                }
                grouped[key]["contributors"] = contributors_value(row.get("contributors"))
                grouped[key]["metadata"] = {
                    key[5:]: value for key, value in row.items() if key.startswith("meta_") and clean_text(value)
                }
                grouped[key]["contents"] = []
                grouped[key]["digital_files"] = []
            if clean_text(row.get("digital_file")):
                grouped[key]["digital_files"].append({
                    "relative_path": row.get("digital_file"),
                    "label": row.get("digital_file_label"),
                    "notes": row.get("digital_file_notes"),
                })
            if clean_text(row.get("content_title")):
                grouped[key]["contents"].append({
                    "title": row.get("content_title"),
                    "work_type": row.get("content_type"),
                    "contributors": contributors_value(row.get("content_contributors")),
                    "page_start": row.get("page_start"),
                    "page_end": row.get("page_end"),
                    "sequence_no": row.get("sequence_no"),
                })
        return list(grouped.values())
    raise ValueError("Import format must be JSON or CSV")


def validate_import(records: list[dict]) -> tuple[list[dict], list[dict]]:
    valid, errors = [], []
    for index, record in enumerate(records, start=1):
        if not isinstance(record, dict):
            errors.append({"row": index, "message": "Record is not an object"})
        elif not clean_text(record.get("title")):
            errors.append({"row": index, "message": "Missing title"})
        else:
            valid.append(record)
    return valid, errors


def export_records() -> list[dict]:
    with connect() as db:
        ids = [r[0] for r in db.execute("SELECT id FROM items ORDER BY title COLLATE NOCASE")]
        records = [get_item(db, item_id) for item_id in ids]
        for record in records:
            for digital_file in record.get("digital_files") or []:
                digital_file.pop("exists", None)
                digital_file.pop("url", None)
        return records


PUBLIC_ITEM_FIELDS = (
    "title", "subtitle", "media_category", "item_type", "publication_date", "publisher", "edition",
    "identifier", "language", "description", "set_name", "volume_label", "volume_number", "stack",
    "shelf_row", "shelf_position",
)
PUBLIC_CONTENT_FIELDS = (
    "title", "work_type", "publication_date", "language", "sequence_no", "page_start", "page_end",
)


def _public_contributors(contributors: list[dict]) -> list[dict]:
    return [
        {key: person[key] for key in ("name", "role") if clean_text(person.get(key))}
        for person in contributors
        if clean_text(person.get("name"))
    ]


def public_export_records() -> list[dict]:
    """Return only the explicitly approved fields used by the public site."""
    records = []
    for item in export_records():
        public_item = {
            field: item[field] for field in PUBLIC_ITEM_FIELDS
            if item.get(field) not in (None, "")
        }
        public_item["contributors"] = _public_contributors(item.get("contributors") or [])
        public_item["contents"] = []
        for content in item.get("contents") or []:
            public_content = {
                field: content[field] for field in PUBLIC_CONTENT_FIELDS
                if content.get(field) not in (None, "")
            }
            public_content["contributors"] = _public_contributors(content.get("contributors") or [])
            public_item["contents"].append(public_content)
        records.append(public_item)
    return records


def build_public_site() -> dict:
    """Generate the static GitHub Pages site from approved public fields."""
    PAGES_DIR.mkdir(parents=True, exist_ok=True)
    for filename in ("index.html", "styles.css", "app.js"):
        shutil.copy2(PUBLIC_SITE_DIR / filename, PAGES_DIR / filename)
    records = public_export_records()
    payload = {
        "version": 1,
        "published_at": utc_now(),
        "items": records,
    }
    (PAGES_DIR / "catalogue.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (PAGES_DIR / ".nojekyll").write_text("", encoding="utf-8")
    return {"items": len(records), "path": str(PAGES_DIR)}


class Handler(BaseHTTPRequestHandler):
    server_version = "ShelfIndex/1.0"

    def log_message(self, fmt, *args):
        print(f"[{self.log_date_time_string()}] {fmt % args}")

    def send_json(self, data, status=200, headers=None):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def send_error_json(self, message, status=400):
        self.send_json({"error": str(message)}, status)

    def read_json(self):
        length = int(self.headers.get("Content-Length", "0"))
        if length > 20 * 1024 * 1024:
            raise ValueError("Request is larger than 20 MB")
        return json.loads(self.rfile.read(length) or b"{}")

    def do_GET(self):
        parsed = urlparse(self.path)
        path, params = parsed.path, parse_qs(parsed.query)
        try:
            if path == "/api/search":
                self.send_json({"items": search_items(
                    params.get("q", [""])[0], params.get("category", [""])[0],
                    params.get("stack", [""])[0], params.get("row", [""])[0],
                )})
                return
            if path == "/api/options":
                self.send_json(options())
                return
            match = re.fullmatch(r"/api/isbn/([^/]+)", path)
            if match:
                self.send_json(lookup_isbn(match.group(1), params.get("refresh", [""])[0] == "1"))
                return
            match = re.fullmatch(r"/api/items/(\d+)", path)
            if match:
                with connect() as db:
                    item = get_item(db, int(match.group(1)))
                self.send_json(item if item else {"error": "Item not found"}, 200 if item else 404)
                return
            if path == "/api/export.json":
                filename = f"shelf-index-{datetime.now().date()}.json"
                self.send_json({"version": 1, "exported_at": utc_now(), "items": export_records()}, headers={
                    "Content-Disposition": f'attachment; filename="{filename}"'
                })
                return
            if path == "/api/backup":
                self.backup_database()
                return
            if path.startswith("/digital/"):
                self.serve_digital(path[len("/digital/"):])
                return
            self.serve_static(path)
        except ValueError as exc:
            self.send_error_json(exc, 400)
        except LookupError as exc:
            self.send_error_json(exc, 404)
        except ConnectionError as exc:
            self.send_error_json(exc, 503)
        except Exception as exc:
            self.send_error_json(exc, 500)

    def do_POST(self):
        try:
            if self.path == "/api/items":
                item_id = save_item(self.read_json())
                self.send_json({"id": item_id}, 201)
                return
            if self.path == "/api/publish":
                self.send_json(build_public_site())
                return
            if self.path in ("/api/import/preview", "/api/import/commit"):
                records = parse_import(self.read_json())
                valid, errors = validate_import(records)
                if self.path.endswith("preview"):
                    self.send_json({"valid": len(valid), "errors": errors, "sample": valid[:5]})
                else:
                    ids = [save_item(record) for record in valid]
                    self.send_json({"imported": len(ids), "ids": ids, "errors": errors})
                return
            self.send_error_json("Not found", 404)
        except (ValueError, json.JSONDecodeError) as exc:
            self.send_error_json(exc)
        except Exception as exc:
            self.send_error_json(exc, 500)

    def do_PUT(self):
        match = re.fullmatch(r"/api/items/(\d+)", self.path)
        if not match:
            self.send_error_json("Not found", 404)
            return
        try:
            item_id = save_item(self.read_json(), int(match.group(1)))
            self.send_json({"id": item_id})
        except LookupError as exc:
            self.send_error_json(exc, 404)
        except (ValueError, json.JSONDecodeError) as exc:
            self.send_error_json(exc)
        except Exception as exc:
            self.send_error_json(exc, 500)

    def do_DELETE(self):
        match = re.fullmatch(r"/api/items/(\d+)", self.path)
        if not match:
            self.send_error_json("Not found", 404)
            return
        item_id = int(match.group(1))
        with connect() as db:
            work_ids = [r[0] for r in db.execute("SELECT work_id FROM item_contents WHERE item_id=?", (item_id,))]
            db.execute("DELETE FROM catalog_fts WHERE item_id=?", (item_id,))
            changed = db.execute("DELETE FROM items WHERE id=?", (item_id,)).rowcount
            for work_id in work_ids:
                db.execute("DELETE FROM works WHERE id=?", (work_id,))
        self.send_json({"deleted": bool(changed)}, 200 if changed else 404)

    def backup_database(self):
        if not DB_PATH.exists():
            self.send_error_json("Database does not exist", 404)
            return
        # SQLite may have recent changes in its WAL file. The backup API folds
        # those changes into one self-contained, consistent database download.
        temporary = tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False)
        temporary.close()
        temporary_path = Path(temporary.name)
        try:
            with connect() as source, sqlite3.connect(temporary_path) as destination:
                source.backup(destination)
            body = temporary_path.read_bytes()
        finally:
            temporary_path.unlink(missing_ok=True)
        self.send_response(200)
        self.send_header("Content-Type", "application/vnd.sqlite3")
        self.send_header("Content-Disposition", f'attachment; filename="shelf-index-{datetime.now().date()}.sqlite3"')
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def serve_static(self, path: str):
        relative = "index.html" if path in ("", "/") else path.lstrip("/")
        requested = (STATIC_DIR / relative).resolve()
        if STATIC_DIR.resolve() not in requested.parents and requested != STATIC_DIR.resolve():
            self.send_error_json("Not found", 404)
            return
        if not requested.is_file():
            requested = STATIC_DIR / "index.html"
        body = requested.read_bytes()
        mime = mimetypes.guess_type(requested.name)[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", f"{mime}; charset=utf-8" if mime.startswith("text/") else mime)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def serve_digital(self, encoded_path: str):
        relative_path = normalize_digital_path(unquote(encoded_path))
        requested = (DIGITAL_LIBRARY_DIR / relative_path).resolve()
        library_root = DIGITAL_LIBRARY_DIR.resolve()
        if library_root not in requested.parents or not requested.is_file():
            self.send_error_json("Digital file not found", 404)
            return
        size = requested.stat().st_size
        mime = mimetypes.guess_type(requested.name)[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(size))
        self.send_header("Cache-Control", "private, no-store")
        self.send_header("Content-Disposition", f"inline; filename*=UTF-8''{quote(requested.name)}")
        self.end_headers()
        with requested.open("rb") as source:
            shutil.copyfileobj(source, self.wfile, length=1024 * 1024)


def main() -> None:
    init_db()
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    url = f"http://{HOST}:{PORT}"
    print(f"Shelf Index is running at {url}")
    print(f"Database: {DB_PATH}")
    print("Press Control-C to stop.")
    if "--no-browser" not in sys.argv:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Shelf Index.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
