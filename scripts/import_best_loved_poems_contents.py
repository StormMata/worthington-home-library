#!/usr/bin/env python3
"""Index item 170 from the 1936 Internet Archive contents scan.

The Archive OCR layout supplies titles and contributor names. Page numbers are
read from locally OCRed crops of the nineteen contents pages because the
Archive's plain text intermittently omits that right-hand column.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
import argparse
import re
import shutil
import xml.etree.ElementTree as ET

import app


ITEM_ID = 170
SOURCE = "https://archive.org/details/bwb_W6-ARA-447"
OCR_XML = Path("/private/tmp/best-loved-djvu.xml")
TOC_DIR = Path("/private/tmp/best-loved-toc-pages")
BACKUP = Path("data/backups/catalogue-before-best-loved-poems-index-2026-10-13.sqlite3")

PAGE_RANGES = {
    14: (3, 16), 15: (17, 43), 16: (44, 70), 17: (71, 99),
    18: (99, 130), 19: (130, 173), 20: (176, 230),
    21: (232, 288), 22: (289, 321), 23: (323, 358),
    24: (359, 388), 25: (389, 430), 26: (431, 466),
    27: (468, 505), 28: (506, 542), 29: (544, 577),
    30: (578, 609), 31: (610, 635), 32: (635, 648),
}

# Two printed numbers were not recognized by any OCR pass.
MANUAL_PAGE_POINTS = {
    (14, 1363): 3,
    (17, 790): 78,
    (19, 1753): 151,
}

TITLE_FIXES = {
    "A Fniend’s Greeting": "A Friend’s Greeting",
    "There Is No. Death": "There Is No Death",
    "Fare Thee Welll": "Fare Thee Well!",
    "A Woman’s Answer to The Vampire _": "A Woman’s Answer to The Vampire",
}

AUTHOR_FIXES = {
    "Sady Morgan": "Lady Morgan",
    "Christina Georgina Rossettt": "Christina Georgina Rossetti",
    "Edgar A, Guest": "Edgar A. Guest",
    "Edward E. Paramore,": "Edward E. Paramore, Jr.",
    "Anson G, Chester": "Anson G. Chester",
    "Matilda C, Edwards": "Matilda C. Edwards",
    "Rey. Elijah Jones": "Rev. Elijah Jones",
    "Rey. G. Anketall Studdert-Kennedy": "Rev. G. A. Studdert-Kennedy",
    "]. G. Baker": "J. G. Baker",
    "James D, Hughes": "James D. Hughes",
}


def join_ocr_hyphenation(text: str) -> str:
    """Join words split only because they crossed a printed line."""
    previous = None
    while text != previous:
        previous = text
        text = re.sub(r"\b([A-Za-z]+)-\s+([a-z][A-Za-z]*)\b", r"\1\2", text)
    return text


def normalize_title(text: str) -> str:
    text = join_ocr_hyphenation(text).strip(" _")
    text = re.sub(r"\s+", " ", text)
    return TITLE_FIXES.get(text, text)


def normalize_author(text: str) -> str:
    text = join_ocr_hyphenation(text)
    text = re.sub(r"\s+", " ", text).strip()
    text = text.replace("Stack )", "Stack)")
    text = re.sub(r"^\]\.", "J.", text)
    return AUTHOR_FIXES.get(text, text)


def xml_rows(obj):
    lines = []
    for line in obj.findall(".//LINE"):
        words = []
        for word in line.findall(".//WORD"):
            coords = list(map(int, word.attrib["coords"].split(",")))
            words.append((*coords, word.text or ""))
        if words:
            y = sum((word[1] + word[3]) / 2 for word in words) / len(words)
            lines.append([y, words])

    rows = []
    for y, words in sorted(lines):
        if rows and abs(y - rows[-1][0]) <= 25:
            rows[-1][1].extend(words)
            rows[-1][0] = sum(
                (word[1] + word[3]) / 2 for word in rows[-1][1]
            ) / len(rows[-1][1])
        else:
            rows.append([y, words[:]])
    return rows


def read_tsv_points(path: Path, scale: float):
    points = []
    for line in path.read_text().splitlines()[1:]:
        columns = line.split("\t")
        if len(columns) < 12 or not columns[11].strip().isdigit():
            continue
        value = int(columns[11].strip())
        y = (float(columns[7]) + float(columns[9]) / 2) * scale + 120
        points.append((y, value))
    return points


def page_points(scan_page: int):
    low, high = PAGE_RANGES[scan_page]
    raw = []
    for suffix, scale in (("pages", 1), ("pages11", 1), ("digits", 0.5)):
        raw.extend(read_tsv_points(TOC_DIR / f"{scan_page}-{suffix}.tsv", scale))
    raw = [(y, value) for y, value in raw if low <= value <= high]
    raw.extend(
        (y, value)
        for (page, y), value in MANUAL_PAGE_POINTS.items()
        if page == scan_page
    )

    clusters = []
    for point in sorted(raw):
        y, _ = point
        if clusters and abs(y - sum(p[0] for p in clusters[-1]) / len(clusters[-1])) < 15:
            clusters[-1].append(point)
        else:
            clusters.append([point])

    result = []
    for cluster in clusters:
        counts = Counter(value for _, value in cluster)
        value = counts.most_common(1)[0][0]
        positions = [y for y, candidate in cluster if candidate == value]
        y = sum(positions) / len(positions)
        # The printed 79 on the third page was consistently read as 78.
        if scan_page == 17 and 880 < y < 930:
            value = 79
        result.append((y, value))
    return result


def contributors(author_text: str):
    author_text = normalize_author(author_text)
    if not author_text:
        return []
    if " Translated by " in author_text:
        author, translator = author_text.split(" Translated by ", 1)
        return [
            {"name": author, "role": "Author"},
            {"name": translator, "role": "Translator"},
        ]
    return [{"name": author_text, "role": "Author"}]


def extract_contents():
    objects = ET.parse(OCR_XML).getroot().findall(".//OBJECT")
    extracted = []

    for scan_page in range(14, 33):
        rows = xml_rows(objects[scan_page])
        pages_by_row = {}
        for y, page_number in page_points(scan_page):
            index = min(range(len(rows)), key=lambda i: abs(rows[i][0] - y))
            distance = abs(rows[index][0] - y)
            if distance < 45 and (
                index not in pages_by_row or distance < pages_by_row[index][1]
            ):
                pages_by_row[index] = (page_number, distance)

        pending_title = []
        pending_author = []
        for index, (_, words) in enumerate(rows):
            words = sorted(words)
            title = " ".join(word[4] for word in words if word[0] < 930).strip()
            author = " ".join(
                word[4] for word in words if 930 <= word[0] < 1450
            ).strip()
            page_number = pages_by_row.get(index, (None, None))[0]
            combined = f"{title} {author}".strip()

            if title == "CONTENTS" or re.fullmatch(r"[xivlcdm]+", title, re.I):
                continue
            if re.match(r"^[IVX]+\.", combined) or combined == "Indexes":
                pending_title.clear()
                pending_author.clear()
                continue

            if title:
                pending_title.append(title)
            if author:
                pending_author.append(author)

            if page_number is not None:
                work_title = normalize_title(" ".join(pending_title))
                author_text = " ".join(pending_author)
                if not work_title:
                    raise RuntimeError(
                        f"Page {scan_page}: page {page_number} has no associated title"
                    )
                extracted.append(
                    {
                        "title": work_title,
                        "work_type": "Poem",
                        "page_start": str(page_number),
                        "contributors": contributors(author_text),
                        "metadata": {"source": SOURCE},
                    }
                )
                pending_title.clear()
                pending_author.clear()

    return extracted


def validate(contents):
    if len(contents) != 587:
        raise RuntimeError(f"Expected 587 indexed pieces; extracted {len(contents)}")
    first, last = contents[0], contents[-1]
    if first["title"] != "Sonnet from the Portuguese" or first["page_start"] != "3":
        raise RuntimeError(f"First-entry verification failed: {first}")
    if last["title"] != "The Year’s at the Spring" or last["page_start"] != "648":
        raise RuntimeError(f"Last-entry verification failed: {last}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    contents = extract_contents()
    validate(contents)
    if args.dry_run:
        for work in contents:
            names = "; ".join(c["name"] for c in work["contributors"])
            print(f'{work["page_start"]}\t{work["title"]}\t{names}')
        print(f"Extracted {len(contents)} pieces.")
        return

    BACKUP.parent.mkdir(parents=True, exist_ok=True)
    if not BACKUP.exists():
        shutil.copy2(app.DB_PATH, BACKUP)

    with app.connect() as db:
        payload = app.get_item(db, ITEM_ID)
        if not payload or payload["title"] != "The Best Loved Poems of the American People":
            raise RuntimeError("Expected item 170 to be the existing book record")
        payload["contents"] = contents
        app.save_item(payload, ITEM_ID)

    print(f"Indexed {len(contents)} pieces in item {ITEM_ID}.")
    print(f"Backup: {BACKUP}")


if __name__ == "__main__":
    main()
