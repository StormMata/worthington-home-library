#!/usr/bin/env python3
"""Add the missing volumes of the 1952 Great Books of the Western World.

The work lists are extracted from a saved copy of the first-edition contents
catalogue on Wikipedia.  The importer intentionally preserves an existing
Volume 39 record and refuses to overwrite any other volume in the set.
"""

from __future__ import annotations

import argparse
import re
import sqlite3
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import app  # noqa: E402


SET_NAME = "Great Books of the Western World"
SOURCE_URL = "https://en.wikipedia.org/wiki/Great_Books_of_the_Western_World"
DEFAULT_SOURCE = Path("/private/tmp/gbww.html")
DEFAULT_BACKUP = ROOT / "data/backups/catalogue-before-great-books-1952-import-2026-10-18.sqlite3"

VOLUME_TITLES = {
    1: "The Great Conversation",
    2: "The Great Ideas: A Syntopicon I",
    3: "The Great Ideas: A Syntopicon II",
    4: "Homer",
    5: "Aeschylus, Sophocles, Euripides, Aristophanes",
    6: "Herodotus, Thucydides",
    7: "Plato",
    8: "Aristotle I",
    9: "Aristotle II",
    10: "Hippocrates, Galen",
    11: "Euclid, Archimedes, Apollonius, Nicomachus",
    12: "Lucretius, Epictetus, Marcus Aurelius",
    13: "Virgil",
    14: "Plutarch",
    15: "Tacitus",
    16: "Ptolemy, Copernicus, Kepler",
    17: "Plotinus",
    18: "Augustine",
    19: "Thomas Aquinas I",
    20: "Thomas Aquinas II",
    21: "Dante",
    22: "Chaucer",
    23: "Machiavelli, Hobbes",
    24: "Rabelais",
    25: "Montaigne",
    26: "Shakespeare I",
    27: "Shakespeare II",
    28: "Gilbert, Galileo, Harvey",
    29: "Cervantes",
    30: "Bacon",
    31: "Descartes, Spinoza",
    32: "Milton",
    33: "Pascal",
    34: "Newton, Huygens",
    35: "Locke, Berkeley, Hume",
    36: "Swift, Sterne",
    37: "Fielding",
    38: "Montesquieu, Rousseau",
    39: "An Inquiry into the Nature and Causes of the Wealth of Nations",
    40: "Gibbon I",
    41: "Gibbon II",
    42: "Kant",
    43: "American State Papers, The Federalist, J. S. Mill",
    44: "Boswell",
    45: "Lavoisier, Fourier, Faraday",
    46: "Hegel",
    47: "Goethe",
    48: "Melville",
    49: "Darwin",
    50: "Marx",
    51: "Tolstoy",
    52: "Dostoevsky",
    53: "William James",
    54: "Freud",
}


def direct_text(element: ET.Element) -> str:
    """Return text preceding an element's first nested list."""
    pieces = [element.text or ""]
    for child in element:
        if child.tag == "ul":
            break
        pieces.extend(child.itertext())
        pieces.append(child.tail or "")
    return " ".join("".join(pieces).split())


def section_for_volume(html: str, volume: int) -> ET.Element:
    match = re.search(
        rf'<section[^>]+aria-labelledby="Volume_{volume}".*?</section>',
        html,
        flags=re.DOTALL,
    )
    if not match:
        raise RuntimeError(f"Could not find first-edition Volume {volume} in source")
    return ET.fromstring(match.group(0))


def split_people(label: str) -> list[str]:
    label = re.sub(r"\s*\((?:translated|rendered).*", "", label).strip()
    if label in {"American State Papers", ""}:
        return []
    if label == "Alexander Hamilton, James Madison, John Jay":
        return ["Alexander Hamilton", "James Madison", "John Jay"]
    if label == "Karl Marx and Friedrich Engels":
        return ["Karl Marx", "Friedrich Engels"]
    return [label]


def translator_from(text: str) -> str | None:
    match = re.search(
        r"(?:translated(?: into English (?:prose|verse))?|rendered into English prose) by (.+?)\)",
        text,
        flags=re.IGNORECASE,
    )
    return match.group(1).strip() if match else None


def clean_work_title(text: str) -> str:
    # Remove a translator statement while retaining meaningful qualifiers such
    # as "Part 1" or "Books IV-V" when they form part of the listed work.
    text = re.sub(
        r"\s*\((?:translated|Translated|rendered|Middle English).*?$",
        "",
        text,
    )
    text = re.sub(
        r",\s*(?:translated|Translated|rendered).*?$",
        ")",
        text,
    )
    return text.strip(" ,")


def add_credit(credits: list[dict], name: str | None, role: str) -> None:
    if not name:
        return
    credit = {"name": name, "role": role}
    if credit not in credits:
        credits.append(credit)


def syntopicon_contents(root: ET.Element) -> list[dict]:
    ul = next((child for child in root if child.tag == "ul"), None)
    if ul is None:
        return []
    text = direct_text(next(child for child in ul if child.tag == "li"))
    topics_text = text.split(":", 1)[1]
    topics = [topic.strip() for topic in topics_text.split(",")]
    topics[-1] = re.sub(r"^and\s+", "", topics[-1])
    return [
        {
            "title": topic,
            "work_type": "Great Idea",
            "contributors": [{"name": "Mortimer J. Adler", "role": "Editor"}],
            "metadata": {"source": SOURCE_URL},
        }
        for topic in topics
    ]


def volume_data(html: str, volume: int) -> tuple[list[dict], list[dict]]:
    root = section_for_volume(html, volume)
    if volume in {2, 3}:
        return [], syntopicon_contents(root)
    if volume == 1:
        return [{"name": "Robert Maynard Hutchins", "role": "Author"}], []

    ul = next((child for child in root if child.tag == "ul"), None)
    if ul is None:
        return [], []

    item_authors: list[dict] = []
    contents: list[dict] = []
    for author_node in (child for child in ul if child.tag == "li"):
        author_label = direct_text(author_node)
        authors = split_people(author_label)
        inherited_translator = translator_from(author_label)
        for author in authors:
            add_credit(item_authors, author, "Author")

        for work_node in author_node.findall(".//li"):
            listed_text = direct_text(work_node)
            title = clean_work_title(listed_text)
            if not title:
                continue
            credits: list[dict] = []
            for author in authors:
                add_credit(credits, author, "Author")
            add_credit(credits, translator_from(listed_text) or inherited_translator, "Translator")
            contents.append(
                {
                    "title": title,
                    "work_type": "Work",
                    "contributors": credits,
                    "metadata": {"source": SOURCE_URL},
                }
            )
    return item_authors, contents


def backup_database(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(f"Backup already exists: {path}")
    with app.connect() as source, sqlite3.connect(path) as destination:
        source.backup(destination)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-html", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--backup", type=Path, default=DEFAULT_BACKUP)
    args = parser.parse_args()

    html = args.source_html.read_text(encoding="utf-8")
    app.init_db()
    with app.connect() as db:
        existing = db.execute(
            "SELECT id, volume_number, title FROM items WHERE set_name=? ORDER BY volume_number",
            (SET_NAME,),
        ).fetchall()
    existing_by_volume = {int(row["volume_number"]): row for row in existing if row["volume_number"] is not None}
    unexpected = sorted(volume for volume in existing_by_volume if volume != 39)
    if unexpected:
        raise RuntimeError(f"Refusing to overwrite existing set volumes: {unexpected}")
    if 39 not in existing_by_volume:
        raise RuntimeError("Existing Volume 39 record was not found")

    # Parse every volume before changing the database so a malformed source
    # cannot leave a partially imported set.
    parsed = {
        volume: volume_data(html, volume)
        for volume in range(1, 55)
        if volume != 39
    }
    backup_database(args.backup)

    created = []
    for volume in range(1, 55):
        if volume == 39:
            continue
        authors, contents = parsed[volume]
        contributors = list(authors)
        add_credit(contributors, "Robert Maynard Hutchins", "Editor")
        add_credit(contributors, "Mortimer J. Adler", "Editor")
        item_id = app.save_item(
            {
                "title": VOLUME_TITLES[volume],
                "media_category": "Book",
                "item_type": "Anthology",
                "publication_date": "1952",
                "publisher": "William Benton",
                "language": "English",
                "description": "First edition of the 54-volume Great Books of the Western World series.",
                "set_name": SET_NAME,
                "volume_number": volume,
                "contributors": contributors,
                "contents": contents,
                "metadata": {
                    "series_edition": "First edition (1952)",
                    "contents_source": SOURCE_URL,
                },
            }
        )
        created.append((volume, item_id, len(contents)))

    print(f"Created {len(created)} volumes; preserved Volume 39 item {existing_by_volume[39]['id']}.")
    print(f"Indexed {sum(count for _, _, count in created)} contained works or topics.")
    print(f"Backup: {args.backup}")


if __name__ == "__main__":
    main()
