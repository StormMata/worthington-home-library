#!/usr/bin/env python3
"""Index the contents of Amy Appleby's Library Of Piano Favorites."""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import app  # noqa: E402


TITLE = "Library Of Piano Favorites"
BACKUP = ROOT / "data/backups/catalogue-before-library-piano-favorites-index-2026-11-18.sqlite3"
SOURCE = "User-supplied table of contents (TOC.pdf)"


def piece(title, composer, page, section, *, role="Composer"):
    contributors = []
    if isinstance(composer, str) and composer:
        contributors = [{"name": composer, "role": role}]
    elif composer:
        contributors = [{"name": name, "role": role} for name in composer]
    return {
        "title": title,
        "work_type": "Piano piece",
        "page_start": str(page),
        "contributors": contributors,
        "metadata": {"section": section, "source": SOURCE},
    }


CONTENTS = [
    # Renaissance and Baroque Favorites
    piece("Minuet in G", "Johann Sebastian Bach", 4, "Renaissance and Baroque Favorites"),
    piece("Prelude No. 2", "Johann Sebastian Bach", 5, "Renaissance and Baroque Favorites"),
    piece("Two-Part Invention No. 8", "Johann Sebastian Bach", 6, "Renaissance and Baroque Favorites"),
    piece("Gavotte", "Johann Sebastian Bach", 8, "Renaissance and Baroque Favorites"),
    piece("Minuet", "Luigi Boccherini", 9, "Renaissance and Baroque Favorites"),
    piece("Le Petit-Rien", "François Couperin", 12, "Renaissance and Baroque Favorites"),
    piece("Air", "George Frideric Handel", 14, "Renaissance and Baroque Favorites"),
    piece("Sarabande", "George Frideric Handel", 16, "Renaissance and Baroque Favorites"),
    piece("Trumpet Voluntary", "Henry Purcell", 17, "Renaissance and Baroque Favorites"),
    piece("Sonata in D Minor", "Domenico Scarlatti", 20, "Renaissance and Baroque Favorites"),

    # Classical Favorites
    piece("Solfeggio", "Carl Philipp Emanuel Bach", 22, "Classical Favorites"),
    piece("Für Elise", "Ludwig van Beethoven", 24, "Classical Favorites"),
    piece("Moonlight Sonata", "Ludwig van Beethoven", 28, "Classical Favorites"),
    piece("Gavotte", "François Joseph Gossec", 32, "Classical Favorites"),
    piece("Allegro in F", "Franz Joseph Haydn", 34, "Classical Favorites"),
    piece("Andante", "Franz Joseph Haydn", 35, "Classical Favorites"),
    piece("Adagio", "Wolfgang Amadeus Mozart", 36, "Classical Favorites"),
    piece("Air", "Wolfgang Amadeus Mozart", 37, "Classical Favorites"),
    piece("Lacrimosa", "Wolfgang Amadeus Mozart", 38, "Classical Favorites"),
    piece("Waltz in G", "Carl Maria von Weber", 40, "Classical Favorites"),
    piece("Allemande", "Carl Maria von Weber", 41, "Classical Favorites"),

    # Romantic Favorites
    piece("Malagueña", "Isaac Albéniz", 42, "Romantic Favorites"),
    piece("Waltz in A-Flat", "Johannes Brahms", 46, "Romantic Favorites"),
    piece("Prelude in E Minor", "Frédéric Chopin", 48, "Romantic Favorites"),
    piece("The Minute Waltz", "Frédéric Chopin", 50, "Romantic Favorites"),
    piece("Polonaise", "Frédéric Chopin", 53, "Romantic Favorites"),
    piece("Pomp and Circumstance", "Edward Elgar", 56, "Romantic Favorites"),
    piece("Liebestraum", "Franz Liszt", 60, "Romantic Favorites"),
    piece("Wedding March", "Felix Mendelssohn", 63, "Romantic Favorites"),
    piece("Dance of the Clowns", "Felix Mendelssohn", 64, "Romantic Favorites"),
    piece("Serenade", "Franz Schubert", 66, "Romantic Favorites"),
    piece("Ave Maria", "Franz Schubert", 68, "Romantic Favorites"),
    piece("The Beautiful Blue Danube", "Johann Strauss", 70, "Romantic Favorites"),
    piece("Piano Concerto No. 1", "Peter Ilyich Tchaikovsky", 76, "Romantic Favorites"),
    piece("Traumerei", "Robert Schumann", 78, "Romantic Favorites"),

    # Impressionist and Modern Favorites
    piece("Rêverie", "Claude Debussy", 79, "Impressionist and Modern Favorites"),
    piece("Clair de Lune", "Claude Debussy", 84, "Impressionist and Modern Favorites"),
    piece("Humoresque", "Antonin Dvořák", 88, "Impressionist and Modern Favorites"),
    piece("Playera", "Enrique Granados", 90, "Impressionist and Modern Favorites"),
    piece("To a Wild Rose", "Edward MacDowell", 94, "Impressionist and Modern Favorites"),
    piece("Narcissus", "Ethelbert Nevin", 96, "Impressionist and Modern Favorites"),
    piece("The Swan", "Camille Saint-Saëns", 100, "Impressionist and Modern Favorites"),
    piece("Trois Gymnopédies", "Erik Satie", 102, "Impressionist and Modern Favorites"),

    # Scenes from the Ballet and Opera
    piece("Pizzicati (from Sylvia)", "Léo Delibes", 108, "Scenes from the Ballet and Opera"),
    piece("Polovtsian Dance (from Prince Igor)", "Alexander Borodin", 110, "Scenes from the Ballet and Opera"),
    piece("Anitra's Dance (from Peer Gynt)", "Edvard Grieg", 111, "Scenes from the Ballet and Opera"),
    piece("March of the Toys (from Babes in Toyland)", "Victor Herbert", 114, "Scenes from the Ballet and Opera"),
    piece("Minuet (from Don Juan)", "Wolfgang Amadeus Mozart", 120, "Scenes from the Ballet and Opera"),
    piece("Musetta's Waltz (from La Bohème)", "Giacomo Puccini", 121, "Scenes from the Ballet and Opera"),
    piece("Can Can (from Orpheus)", "Jacques Offenbach", 124, "Scenes from the Ballet and Opera"),
    piece("The Young Prince and the Young Princess (from Sheherazade)", "Nikolai Rimsky-Korsakov", 128, "Scenes from the Ballet and Opera"),
    piece("I'm Called Little Buttercup (from H.M.S. Pinafore)", "Arthur Sullivan", 129, "Scenes from the Ballet and Opera"),
    piece("Waltz of the Flowers (from The Nutcracker)", "Peter Ilyich Tchaikovsky", 132, "Scenes from the Ballet and Opera"),
    piece("Grand March (from Aida)", "Giuseppe Verdi", 134, "Scenes from the Ballet and Opera"),
    piece("Bridal Chorus (from Lohengrin)", "Richard Wagner", 136, "Scenes from the Ballet and Opera"),

    # Ragtime and Novelty Favorites
    piece("Maple Leaf Rag", "Scott Joplin", 138, "Ragtime and Novelty Favorites"),
    piece("Nola", "Felix Arndt", 141, "Ragtime and Novelty Favorites"),
    piece("12th Street Rag", "Euday L. Bowman", 146, "Ragtime and Novelty Favorites"),
    piece("The Chevy Chase", "Eubie Blake", 150, "Ragtime and Novelty Favorites"),
    piece("Bugle Call Rag", "Eubie Blake", 154, "Ragtime and Novelty Favorites"),
    piece("Kitten on the Keys", "Zez Confrey", 158, "Ragtime and Novelty Favorites"),
    piece("You Tell 'Em Ivories", "Zez Confrey", 162, "Ragtime and Novelty Favorites"),
    piece("Rialto Ripples", "George Gershwin", 166, "Ragtime and Novelty Favorites"),
    piece("The Banjo", "Louis Moreaux Gottschalk", 170, "Ragtime and Novelty Favorites"),
    piece("The Entertainer", "Scott Joplin", 178, "Ragtime and Novelty Favorites"),
    piece("Solace", "Scott Joplin", 182, "Ragtime and Novelty Favorites"),
    piece("Jelly Roll Blues", "Jelly Roll Morton", 186, "Ragtime and Novelty Favorites"),
    piece("The Whistler and His Dog", "Arthur Pryor", 190, "Ragtime and Novelty Favorites"),
    piece("The Stars and Stripes Forever", "John Philip Sousa", 194, "Ragtime and Novelty Favorites"),

    # Music of Many Lands
    piece("Amazing Grace", "American folk hymn", 198, "Music of Many Lands", role="Traditional source"),
    piece("El Choclo", "A. G. Villoldo", 200, "Music of Many Lands"),
    piece("Country Gardens", "English morris dance", 202, "Music of Many Lands", role="Traditional source"),
    piece("Greensleeves (What Child Is This)", "English ballad", 204, "Music of Many Lands", role="Traditional source"),
    piece("Santa Lucia", "Italian boat song", 205, "Music of Many Lands", role="Traditional source"),
    piece("Havah Nagilah", "Hebrew hora", 206, "Music of Many Lands", role="Traditional source"),
    piece("Danny Boy (Londonderry Air)", "Irish folk song", 208, "Music of Many Lands", role="Traditional source"),
    piece("Mexican Hat Dance", "Felice Partichala", 210, "Music of Many Lands"),
    piece("Dark Eyes", "Russian Gypsy song", 212, "Music of Many Lands", role="Traditional source"),
    piece("Finlandia", "Jan Sibelius", 214, "Music of Many Lands"),
    piece("Auld Lang Syne", "Scottish air", 215, "Music of Many Lands", role="Traditional source"),
    piece("Carnival of Venice", "Venetian melody", 216, "Music of Many Lands", role="Traditional source"),

    # Golden Hits and Showstoppers
    piece("I Love a Piano", "Irving Berlin", 218, "Golden Hits and Showstoppers"),
    piece("A Pretty Girl Is Like a Melody", "Irving Berlin", 220, "Golden Hits and Showstoppers"),
    piece("The Darktown Strutters' Ball", "Shelton Brooks", 222, "Golden Hits and Showstoppers"),
    piece("My Melancholy Baby", "Ernie Burnett", 223, "Golden Hits and Showstoppers"),
    piece("Give My Regards to Broadway", "George M. Cohan", 224, "Golden Hits and Showstoppers"),
    piece("After You've Gone", ["Creamer", "Layton"], 226, "Golden Hits and Showstoppers"),
    piece("St. Louis Blues", "W. C. Handy", 227, "Golden Hits and Showstoppers"),
    piece("Look for the Silver Lining", "Jerome Kern", 230, "Golden Hits and Showstoppers"),
    piece("Pretty Baby", ["Gus Kahn", "T. Jackson", "Egbert van Alstyne"], 232, "Golden Hits and Showstoppers"),
    piece("I'm Forever Blowing Bubbles", ["Jaan Kenbrovin", "J. W. Kellette"], 233, "Golden Hits and Showstoppers"),
    piece("You Made Me Love You", ["James V. Monaco", "Joe McCarthy"], 234, "Golden Hits and Showstoppers"),
    piece("Shine On Harvest Moon", ["Jack Norworth", "Nora Bayes"], 236, "Golden Hits and Showstoppers"),
    piece("Dallas Blues", ["Hart A. Wand", "L. Garrett"], 237, "Golden Hits and Showstoppers"),
    piece("Moonlight Bay", "Percy Wenrich", 238, "Golden Hits and Showstoppers"),
    piece("In the Shade of the Old Apple Tree", ["Harry H. Williams", "Egbert van Alstyne"], 239, "Golden Hits and Showstoppers"),
]


def backup_database() -> None:
    BACKUP.parent.mkdir(parents=True, exist_ok=True)
    if BACKUP.exists():
        raise FileExistsError(f"Backup already exists: {BACKUP}")
    with app.connect() as source, sqlite3.connect(BACKUP) as destination:
        source.backup(destination)


def main() -> None:
    if len(CONTENTS) != 96:
        raise RuntimeError(f"Expected 96 contents entries, found {len(CONTENTS)}")
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
