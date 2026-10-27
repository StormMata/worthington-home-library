#!/usr/bin/env python3
"""Add Volumes 2–10 of Encyclopaedia Britannica's Great Ideas Program."""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import app  # noqa: E402


SET_NAME = "The Great Ideas Program"
BACKUP = ROOT / "data/backups/catalogue-before-great-ideas-program-import-2026-10-18.sqlite3"
SOURCE = "https://openlibrary.org/books/OL2282629M/The_Great_ideas_program."

VOLUMES = {
    2: {
        "title": "The Development of Political Theory and Government",
        "year": "1959",
        "authors": ["Mortimer J. Adler", "Peter Wolff"],
    },
    3: {
        "title": "Foundations of Science and Mathematics",
        "year": "1960",
        "authors": ["Mortimer J. Adler", "Peter Wolff"],
    },
    4: {
        "title": "Religion and Theology",
        "year": "1961",
        "authors": ["Mortimer J. Adler", "Seymour Cain"],
    },
    5: {
        "title": "Philosophy of Law and Jurisprudence",
        "year": "1961",
        "authors": ["Mortimer J. Adler", "Peter Wolff"],
    },
    6: {
        "title": "Imaginative Literature I: From Homer to Shakespeare",
        "year": "1961",
        "authors": ["Mortimer J. Adler", "Seymour Cain"],
    },
    7: {
        "title": "Imaginative Literature II: From Cervantes to Dostoevsky",
        "year": "1962",
        "authors": ["Mortimer J. Adler", "Seymour Cain"],
    },
    8: {
        "title": "Ethics: The Study of Moral Values",
        "year": "1962",
        "authors": ["Mortimer J. Adler", "Seymour Cain"],
    },
    9: {
        "title": "Biology, Psychology, and Medicine",
        "year": "1963",
        "authors": ["Mortimer J. Adler", "V. J. McGill"],
    },
    10: {
        "title": "Philosophy",
        "year": "1963",
        "authors": ["Mortimer J. Adler", "Seymour Cain"],
    },
}


def backup_database() -> None:
    BACKUP.parent.mkdir(parents=True, exist_ok=True)
    if BACKUP.exists():
        raise FileExistsError(f"Backup already exists: {BACKUP}")
    with app.connect() as source, sqlite3.connect(BACKUP) as destination:
        source.backup(destination)


def main() -> None:
    app.init_db()
    with app.connect() as db:
        existing = db.execute(
            "SELECT id, volume_number, title FROM items WHERE set_name=? ORDER BY volume_number",
            (SET_NAME,),
        ).fetchall()
    if existing:
        found = [int(row["volume_number"]) for row in existing if row["volume_number"] is not None]
        raise RuntimeError(f"Refusing to create duplicate set records; existing volumes: {found}")

    backup_database()
    created = []
    for volume, record in VOLUMES.items():
        item_id = app.save_item(
            {
                "title": record["title"],
                "media_category": "Book",
                "item_type": "Anthology",
                "publication_date": record["year"],
                "publisher": "Encyclopaedia Britannica, Inc.",
                "language": "English",
                "description": (
                    "A volume in The Great Ideas Program, a guided reading companion "
                    "to Great Books of the Western World."
                ),
                "set_name": SET_NAME,
                "volume_number": volume,
                "contributors": [
                    {"name": name, "role": "Author"} for name in record["authors"]
                ],
                "metadata": {
                    "series_publication_span": "1959–1963",
                    "bibliographic_source": SOURCE,
                },
            }
        )
        created.append((volume, item_id))

    print(f"Created {len(created)} Great Ideas Program volumes: 2–10.")
    print(f"Backup: {BACKUP}")


if __name__ == "__main__":
    main()
