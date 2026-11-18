#!/usr/bin/env python3
"""Index Volume I of The Scribner Radio Music Library."""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import app  # noqa: E402


TITLE = "Classic and Romantic Compositions"
BACKUP = ROOT / "data/backups/catalogue-before-classic-romantic-index-2026-11-18.sqlite3"
SOURCE = "User-supplied table of contents (TOC.pdf)"


def piece(title, composer, page):
    return {
        "title": title,
        "work_type": "Piano composition",
        "page_start": str(page),
        "contributors": [{"name": composer, "role": "Composer"}],
        "metadata": {"source": SOURCE},
    }


# The printed contents include several alternate-title cross-references to the
# same composition and page. Each physical composition is represented once,
# with both names retained in the searchable title where useful.
CONTENTS = [
    piece("Adagio Cantabile (Pathétique Sonata)", "Ludwig van Beethoven", 30),
    piece('Adagio ("Moonlight" Sonata)', "Ludwig van Beethoven", 21),
    piece("Adagio (Octet, Op. 166)", "Franz Schubert", 100),
    piece("Air for the G String", "Johann Sebastian Bach", 16),
    piece("Andante (Fifth Symphony)", "Ludwig van Beethoven", 40),
    piece("Andante (Kreutzer Sonata)", "Ludwig van Beethoven", 26),
    piece("Andante (Orfeo e Euridice)", "Christoph Willibald Gluck", 47),
    piece("Andante (Surprise Symphony)", "Joseph Haydn", 76),
    piece("Aufschwung (Soaring), Op. 12", "Robert Schumann", 206),
    piece("Ballet Music (Rosamunde)", "Franz Schubert", 110),
    piece("Bourrée (Second Violin Sonata)", "Johann Sebastian Bach", 18),
    piece("Bourrée (Armide)", "Christoph Willibald Gluck", 51),
    piece("Bourrée", "George Frideric Handel", 60),
    piece("Caprice (Alceste)", "Christoph Willibald Gluck", 54),
    piece("Confidence", "Felix Mendelssohn", 170),
    piece("Consolation, No. 5", "Franz Liszt", 232),
    piece("Consolation", "Felix Mendelssohn", 172),
    piece("Dream of Love (Liebestraum)", "Franz Liszt", 234),
    piece("Scotch Dances (Écossaisen)", "Ludwig van Beethoven", 34),
    piece("Entr'acte (Rosamunde)", "Franz Schubert", 107),
    piece("Für Elise", "Ludwig van Beethoven", 27),
    piece("Gavotte (Sixth Violin Sonata)", "Johann Sebastian Bach", 12),
    piece("Gavotte (Iphigenie)", "Christoph Willibald Gluck", 48),
    piece("Gavotte", "François-Joseph Gossec", 56),
    piece("Gavotte", "Giovanni Battista Martini", 84),
    piece("German Dance", "Carl Ditters von Dittersdorf", 58),
    piece("Gipsy Rondo", "Joseph Haydn", 64),
    piece("Hark! Hark! the Lark!", "Franz Schubert", 116),
    piece("Hungarian Rhapsody, No. 2", "Franz Liszt", 240),
    piece("Invitation to the Dance", "Carl Maria von Weber", 160),
    piece("Kamennoi-Ostrow, Op. 10, No. 22", "Anton Rubinstein", 222),
    piece("Loure (Cello Suite)", "Johann Sebastian Bach", 8),
    piece("Marche Militaire", "Franz Schubert", 113),
    piece("Mazurka, Op. 7, No. 1", "Frédéric Chopin", 158),
    piece("Melody in F", "Anton Rubinstein", 216),
    piece("Minuets (2d Partitur)", "Johann Sebastian Bach", 10),
    piece("Minuet in G", "Ludwig van Beethoven", 24),
    piece("Minuet in A", "Luigi Boccherini", 88),
    piece("Minuet (Symphony in D)", "Joseph Haydn", 74),
    piece("Minuet (Divertimento, No. 1)", "Wolfgang Amadeus Mozart", 132),
    piece("Minuet (Don Juan)", "Wolfgang Amadeus Mozart", 122),
    piece("Minuet (Sonata, Op. 78)", "Franz Schubert", 104),
    piece('"Minute" Waltz, Op. 64, No. 1', "Frédéric Chopin", 149),
    piece("Moment Musical, Op. 94, No. 3", "Franz Schubert", 102),
    piece("Nachtstück, Op. 23, No. 4", "Robert Schumann", 199),
    piece("Nocturne, Op. 9, No. 2", "Frédéric Chopin", 137),
    piece("Nocturne, Op. 55, No. 1", "Frédéric Chopin", 140),
    piece("Nocturne in B-flat", "John Field", 135),
    piece("Prelude in C", "Johann Sebastian Bach", 6),
    piece("Prelude, Op. 28, No. 4", "Frédéric Chopin", 152),
    piece("Prelude, Op. 28, No. 5", "Frédéric Chopin", 153),
    piece("Prelude, Op. 28, No. 6", "Frédéric Chopin", 154),
    piece("Prelude, Op. 28, No. 7", "Frédéric Chopin", 155),
    piece("Prelude, Op. 28, No. 23", "Frédéric Chopin", 156),
    piece("Romance", "Anton Rubinstein", 230),
    piece("Rondo Capriccioso, Op. 14", "Felix Mendelssohn", 182),
    piece("Sarabande", "George Frideric Handel", 62),
    piece("Slumber Song (Schlummerlied), Op. 124, No. 16", "Robert Schumann", 202),
    piece("Serenade (Quartet)", "Joseph Haydn", 71),
    piece("Serenade", "Franz Schubert", 118),
    piece("Sonata in C (First Movement)", "Wolfgang Amadeus Mozart", 128),
    piece("Spinning Song", "Felix Mendelssohn", 173),
    piece("Spring Song", "Felix Mendelssohn", 178),
    piece("Le Tambourin", "Jean-Philippe Rameau", 82),
    piece("Tempo di Ballo", "Domenico Scarlatti", 80),
    piece("Toreador et Andalouse", "Anton Rubinstein", 213),
    piece("Träumerei", "Robert Schumann", 198),
    piece("Turkish March (Ruins of Athens)", "Ludwig van Beethoven", 44),
    piece("Turkish March", "Wolfgang Amadeus Mozart", 124),
    piece("Unfinished Symphony", "Franz Schubert", 91),
    piece("Waltz, Op. 34, No. 2", "Frédéric Chopin", 144),
    piece("Waltzes, Op. 9a", "Franz Schubert", 96),
    piece("Why? (Warum?), Op. 12", "Robert Schumann", 212),
    piece("Wedding March", "Felix Mendelssohn", 193),
]


def backup_database() -> None:
    BACKUP.parent.mkdir(parents=True, exist_ok=True)
    if BACKUP.exists():
        raise FileExistsError(f"Backup already exists: {BACKUP}")
    with app.connect() as source, sqlite3.connect(BACKUP) as destination:
        source.backup(destination)


def main() -> None:
    if len(CONTENTS) != 74:
        raise RuntimeError(f"Expected 74 distinct contents entries, found {len(CONTENTS)}")
    app.init_db()
    with app.connect() as db:
        rows = db.execute(
            "SELECT id FROM items WHERE title=? COLLATE NOCASE",
            (TITLE,),
        ).fetchall()
        if len(rows) != 1:
            raise RuntimeError(f"Expected one matching item, found {len(rows)}")
        item_id = rows[0]["id"]
        existing_count = db.execute(
            "SELECT count(*) FROM item_contents WHERE item_id=?", (item_id,)
        ).fetchone()[0]
    if existing_count:
        raise RuntimeError(f"Item {item_id} already has {existing_count} indexed works")

    with app.connect() as db:
        item = app.get_item(db, item_id)
    backup_database()
    item["contents"] = CONTENTS
    app.save_item(item, item_id)
    print(f"Indexed {len(CONTENTS)} works for item {item_id}: {TITLE}")
    print(f"Backup: {BACKUP}")


if __name__ == "__main__":
    main()
