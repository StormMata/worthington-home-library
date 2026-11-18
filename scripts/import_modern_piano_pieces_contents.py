#!/usr/bin/env python3
"""Index Modern Piano Pieces the Whole World Plays (1917)."""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import app  # noqa: E402


TITLE = "Modern Piano Pieces the Whole World Plays"
BACKUP = ROOT / "data/backups/catalogue-before-modern-piano-pieces-index-2026-11-18.sqlite3"
SOURCE = "User-supplied alphabetical index (TOC.pdf)"


def piece(title, composer, page):
    return {
        "title": title,
        "work_type": "Piano composition",
        "page_start": str(page),
        "contributors": [{"name": composer, "role": "Composer"}],
        "metadata": {"source": SOURCE},
    }


CONTENTS = [
    piece("À l'Église", "Gabriel Pierné", 148),
    piece("Alla Mazurka", "Nemerowsky", 138),
    piece("An Album Leaf", "Richard Wagner", 246),
    piece("Angelus (Scènes Pittoresques)", "Jules Massenet", 124),
    piece("At Sunset", "Edward MacDowell", 75),
    piece("Au Bord du Danube", "André Wormser", 250),
    piece("Auf stillem Waldespfad", "Richard Strauss", 219),
    piece("Au Matin", "Benjamin Godard", 58),
    piece("Barcarolle, Op. 33", "Adolf Jensen", 96),
    piece("Barcarolle, Op. 62, No. 4", "Xaver Scharwenka", 194),
    piece("Beim Kränzewinden", "Isidor Seiss", 204),
    piece("Berceuse", "August Delbrück", 39),
    piece("Berceuse, Op. 16, No. 1", "Alexander von Fielitz", 244),
    piece("Berceuse, Op. 26, No. 7", "Eduard Schütt", 200),
    piece("Canzonetta", "César Cui", 32),
    piece("Chanson Triste", "Pyotr Ilyich Tchaikovsky", 236),
    piece("Characteristique", "Christian Sinding", 216),
    piece("Consolation, Op. 19, No. 6", "Theodor Leschetizky", 112),
    piece("Consolation No. 2", "Franz Liszt", 120),
    piece("Cradle Song", "Alexander Ilyinsky", 90),
    piece("Crescendo", "Eduard Lassen", 162),
    piece("Élégie, Op. 1, No. 3", "Vladimir Youferoff", 254),
    piece("En berçant", "Eduard Schütt", 214),
    piece("Erotikon", "Edvard Grieg", 70),
    piece("Gavotte Moderne", "Berthold Tours", 226),
    piece("Gipsy Dance, Op. 20", "Pablo de Sarasate", 190),
    piece("La Gondola", "Adolf von Henselt", 82),
    piece("Habanera", "Emmanuel Chabrier", 20),
    piece("Humoreske, Op. 10, No. 2", "Pyotr Ilyich Tchaikovsky", 232),
    piece("In the Wood", "Vincenzo Poldini", 152),
    piece("Klavierstück", "Salomon Jadassohn", 92),
    piece("Liebestraum", "Franz Liszt", 114),
    piece("Lullaby", "Halfdan Kjerulf", 106),
    piece("Madrigal", "Théodore Lack", 108),
    piece("Mazurka, Op. 21, No. 1", "Camille Saint-Saëns", 176),
    piece("Mélodie, Op. 18, No. 1", "Moritz Moszkowski", 135),
    piece("Mélodie, Op. 16, No. 2", "Ignacy Jan Paderewski", 144),
    piece("Menuett, Op. 33", "Adolf Jensen", 100),
    piece("Moment Musical", "Philipp Scharwenka", 181),
    piece("Murmuring Brook", "Vincenzo Poldini", 154),
    piece("Nachtstück, Op. 23, No. 4", "Robert Schumann", 196),
    piece("Nocturne", "Alexander Borodin", 8),
    piece("Papillon", "Edvard Grieg", 72),
    piece("Petite Mazurka", "Vasily Sapellnikoff", 184),
    piece("Petite Valse, Op. 10, No. 2", "Genari Karganoff", 104),
    piece("Près de l'Eau", "Felix Blumenfeld", 6),
    piece("Rêverie", "Claude Debussy", 34),
    piece("Rêverie", "Arthur Hervey", 86),
    piece("Rêverie, Op. 34, No. 5", "Eduard Schütt", 210),
    piece("Romance", "Sergei Rachmaninoff", 156),
    piece("Romance, Op. 2, No. 2", "Joachim Raff", 158),
    piece("Romance, Op. 44, No. 1", "Anton Rubinstein", 165),
    piece("Romance, Op. 5", "Pyotr Ilyich Tchaikovsky", 239),
    piece("Romance sans paroles", "Gabriel Fauré", 55),
    piece("Scotch Poem", "Edward MacDowell", 78),
    piece("Sérénade", "Alexander Borodin", 11),
    piece("Sérénade", "Ole Olsen", 142),
    piece("Silhouette, Op. 8, No. 2", "Antonín Dvořák", 47),
    piece("Silhouette, Op. 8, No. 4", "Antonín Dvořák", 52),
    piece("Song Without Words", "Camille Saint-Saëns", 172),
    piece("Souvenir", "František Drdla", 42),
    piece("Souvenir, Op. 10, No. 1", "Genari Karganoff", 102),
    piece("Spanish Dance, Op. 12, No. 1", "Moritz Moszkowski", 132),
    piece("Spring Song", "Gustav Merkel", 128),
    piece("Les Sylvains", "Cécile Chaminade", 26),
    piece("Toreador et Andalouse", "Anton Rubinstein", 168),
    piece("Träumerei", "Richard Strauss", 224),
    piece("Valse Gracieuse", "Antonín Dvořák", 48),
    piece("Valse Lente, Op. 12, No. 2", "Eduard Schütt", 206),
    piece("Villanesca", "Enrique Granados", 64),
    piece("Waltzes, Op. 39 (Selected)", "Johannes Brahms", 14),
    piece("Warum?, Op. 12, No. 3", "Robert Schumann", 198),
]


def backup_database() -> None:
    BACKUP.parent.mkdir(parents=True, exist_ok=True)
    if BACKUP.exists():
        raise FileExistsError(f"Backup already exists: {BACKUP}")
    with app.connect() as source, sqlite3.connect(BACKUP) as destination:
        source.backup(destination)


def main() -> None:
    if len(CONTENTS) != 72:
        raise RuntimeError(f"Expected 72 contents entries, found {len(CONTENTS)}")
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
