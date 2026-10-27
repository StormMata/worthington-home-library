#!/usr/bin/env python3
"""Index the photographed table of contents for catalogue item 171."""

from pathlib import Path
import shutil

import app


ITEM_ID = 171
BACKUP = Path("data/backups/catalogue-before-english-poetry-index-2026-10-13.sqlite3")


def entry(title, page, author=None, work_type="Poem"):
    result = {
        "title": title,
        "work_type": work_type,
        "page_start": str(page),
        "contributors": [],
        "metadata": {},
    }
    if author:
        result["contributors"] = [{"name": author, "role": "Author"}]
    return result


contents = [
    entry("Preface", "v", "Roberta Florence Brinkley", "Preface"),
    entry("The Seventeenth Century in England", 1, "Roberta Florence Brinkley", "Essay"),

    entry("Song", 28, "John Donne"),
    entry("The Indifferent", 29, "John Donne"),
    entry("Woman's Constancy", 29, "John Donne"),
    entry("The Legacy", 30, "John Donne"),
    entry("The Message", 31, "John Donne"),
    entry("Love's Deity", 32, "John Donne"),
    entry("The Ecstasy", 32, "John Donne"),
    entry("Lovers' Infiniteness", 35, "John Donne"),
    entry("The Anniversary", 36, "John Donne"),
    entry("The Good-Morrow", 37, "John Donne"),
    entry("The Canonization", 38, "John Donne"),
    entry("The Undertaking", 39, "John Donne"),
    entry("Elegy XVII—On His Mistress", 40, "John Donne"),
    entry("Song", 42, "John Donne"),
    entry("A Valediction Forbidding Mourning", 43, "John Donne"),
    entry("The Funeral", 44, "John Donne"),
    entry("The Relique", 45, "John Donne"),
    entry("Twicknam Garden", 46, "John Donne"),
    entry("A Fever", 47, "John Donne"),
    entry("An Anatomy of the World", 48, "John Donne"),
    entry("Holy Sonnets", 59, "John Donne"),
    entry("A Hymn to God the Father", 63, "John Donne"),

    entry("Oberon, the Fairy Prince", 70, "Ben Jonson"),
    entry("Song, To Celia", 81, "Ben Jonson"),
    entry("Hymn", 82, "Ben Jonson"),
    entry("A Song", 83, "Ben Jonson"),
    entry("[Simplex Munditiis]", 83, "Ben Jonson"),
    entry("From—A Celebration of Charis", 84, "Ben Jonson"),
    entry("From—The Sad Shepherd", 85, "Ben Jonson"),
    entry("On My First Daughter", 85, "Ben Jonson"),
    entry("On My First Son", 85, "Ben Jonson"),
    entry("Epitaph on Elizabeth, L. H.", 86, "Ben Jonson"),
    entry("Epitaph on S[alathiel] P[avy]", 86, "Ben Jonson"),
    entry("From—A Pindaric Ode on the Death of Sir H. Morison", 87, "Ben Jonson"),
    entry("To the Memory of My Beloved Master William Shakespeare", 88, "Ben Jonson"),
    entry("To William Camden", 90, "Ben Jonson"),
    entry("On Lucy, Countess of Bedford", 91, "Ben Jonson"),
    entry("To Penshurst", 91, "Ben Jonson"),
    entry("Ode to Himself", 94, "Ben Jonson"),

    entry("The Apollyonists, Canto I", 99, "Phineas Fletcher"),
    entry("Christ's Triumph after Death", 115, "Giles Fletcher"),
    entry("Sonnets", 133, "William Drummond"),
    entry("Madrigals", 136, "William Drummond"),
    entry("Song", 137, "William Drummond"),
    entry("An Hymn of the Ascension", 138, "William Drummond"),
    entry("From—The Shepherd's Hunting", 144, "George Wither"),
    entry("From—Fair Virtue", 147, "George Wither"),
    entry("The Author's Resolution in a Sonnet", 150, "George Wither"),
    entry("From—The Shepherd's Pipe", 154, "William Browne"),
    entry("From—Britannia's Pastorals", 160, "William Browne"),

    entry("His Prayer to Ben Jonson", 165, "Robert Herrick"),
    entry("An Ode for Him", 165, "Robert Herrick"),
    entry("To the Water Nymphs Drinking at the Fountain", 166, "Robert Herrick"),
    entry("Delight in Disorder", 166, "Robert Herrick"),
    entry("The Night Piece, to Julia", 167, "Robert Herrick"),
    entry("The Argument of His Book", 167, "Robert Herrick"),
    entry("To Daffodils", 168, "Robert Herrick"),
    entry("To Blossoms", 168, "Robert Herrick"),
    entry("To Primroses Filled with Morning Dew", 169, "Robert Herrick"),
    entry("Corinna's Going A-Maying", 170, "Robert Herrick"),
    entry("To Meadows", 172, "Robert Herrick"),
    entry("His Answer to a Question", 173, "Robert Herrick"),
    entry("Upon the Loss of His Mistresses", 173, "Robert Herrick"),
    entry("To the Virgins, to Make Much of Time", 174, "Robert Herrick"),
    entry("To Anthea, Who May Command Him Anything", 174, "Robert Herrick"),
    entry("To the Rose", 175, "Robert Herrick"),
    entry("To Music, to Becalm His Fever", 176, "Robert Herrick"),
    entry("The Country Life", 177, "Robert Herrick"),
    entry("His Content in the Country", 179, "Robert Herrick"),
    entry("His Grange, or Private Wealth", 180, "Robert Herrick"),
    entry("Upon Prue, His Maid", 181, "Robert Herrick"),
    entry("A Ternary of Littles", 181, "Robert Herrick"),
    entry("Ceremonies for Christmas", 182, "Robert Herrick"),
    entry("Ceremonies for Candlemas Eve", 182, "Robert Herrick"),
    entry("Ceremony upon Candlemas Eve", 183, "Robert Herrick"),
    entry("The Ceremonies for Candlemas Day", 183, "Robert Herrick"),
    entry("The Wake", 184, "Robert Herrick"),
    entry("The Hock-Cart, or Harvest Home", 184, "Robert Herrick"),
    entry("The Wassail", 186, "Robert Herrick"),
    entry("Oberon's Feast", 187, "Robert Herrick"),
    entry("The Hag", 189, "Robert Herrick"),
    entry("The Fairies", 190, "Robert Herrick"),
    entry("Discontents in Devon", 190, "Robert Herrick"),
    entry("His Return to London", 190, "Robert Herrick"),
    entry("His Prayer for Absolution", 191, "Robert Herrick"),
    entry("Another Grace for a Child", 191, "Robert Herrick"),
    entry("To Find God", 192, "Robert Herrick"),
    entry("A Thanksgiving to God for His House", 192, "Robert Herrick"),
    entry("His Litany to the Holy Spirit", 194, "Robert Herrick"),
    entry("The White Island, or Place of the Blest", 196, "Robert Herrick"),
    entry("To Death", 196, "Robert Herrick"),
    entry("To Robin Redbreast", 197, "Robert Herrick"),
    entry("The Pillar of Fame", 197, "Robert Herrick"),

    entry("Book I—Emblem XV", 200, "Francis Quarles"),
    entry("Book II—Emblem IV", 203, "Francis Quarles"),
    entry("Book IV—Emblem III", 206, "Francis Quarles"),

    entry("The Resolve", 213, "George Herbert"),
    entry("Love [1]", 213, "George Herbert"),
    entry("Jordan", 214, "George Herbert"),
    entry("Sin", 214, "George Herbert"),
    entry("The Pulley", 215, "George Herbert"),
    entry("Peace", 216, "George Herbert"),
    entry("The Collar", 217, "George Herbert"),
    entry("The Quip", 218, "George Herbert"),
    entry("The Glance", 219, "George Herbert"),
    entry("Affliction", 220, "George Herbert"),
    entry("Discipline", 222, "George Herbert"),
    entry("Love [2]", 223, "George Herbert"),
    entry("The Pearl", 224, "George Herbert"),
    entry("The Flower", 225, "George Herbert"),
    entry("The Elixir", 227, "George Herbert"),
    entry("The Church Windows", 228, "George Herbert"),
    entry("Church Music", 228, "George Herbert"),
    entry("The Altar", 229, "George Herbert"),
    entry("Sunday", 229, "George Herbert"),
    entry("Easter Wings", 232, "George Herbert"),
    entry("Virtue", 232, "George Herbert"),

    entry("An Elegy upon the Death of the Dean of St. Paul's, Dr. John Donne", 236, "Thomas Carew"),
    entry("To Ben Jonson", 239, "Thomas Carew"),
    entry("The Spring", 240, "Thomas Carew"),
    entry("Upon a Ribbon Tied about His Arm by a Lady", 241, "Thomas Carew"),
    entry("A Song", 242, "Thomas Carew"),
    entry("Mediocrity in Love Rejected", 243, "Thomas Carew"),
    entry("To My Inconstant Mistress", 243, "Thomas Carew"),
    entry("A Cruel Mistress", 244, "Thomas Carew"),
    entry("Disdain Returned", 244, "Thomas Carew"),
    entry("Persuasions to Enjoy", 245, "Thomas Carew"),
    entry("Ingrateful Beauty Threatened", 246, "Thomas Carew"),
    entry("To A. L., Persuasions to Love", 246, "Thomas Carew"),

    entry("Song", 252, "Edmund Waller"),
    entry("On a Girdle", 253, "Edmund Waller"),
    entry("The Self-banished", 253, "Edmund Waller"),
    entry("At Penshurst", 254, "Edmund Waller"),
    entry("To Mr. Henry Lawes", 255, "Edmund Waller"),
    entry("Of the Last Verses in the Book", 256, "Edmund Waller"),

    entry("Song on May Morning", 262, "John Milton"),
    entry("On His Birthday", 262, "John Milton"),
    entry("Lycidas", 263, "John Milton"),
    entry("To the Lord General Cromwell", 270, "John Milton"),
    entry("On the Late Massacre in Piedmont", 270, "John Milton"),
    entry("On His Blindness", 271, "John Milton"),
    entry("To Cyriack Skinner [II]", 271, "John Milton"),
    entry("On His Deceased Wife", 272, "John Milton"),
    entry("Samson Agonistes", 273, "John Milton", "Drama"),

    entry("Song [from Aglaura]", 325, "Sir John Suckling"),
    entry("[Constancy]", 326, "Sir John Suckling"),
    entry("A Song to a Lute", 327, "Sir John Suckling"),
    entry("Song", 327, "Sir John Suckling"),
    entry("[The Siege]", 328, "Sir John Suckling"),
    entry("A Doubt of Martyrdom", 329, "Sir John Suckling"),
    entry("Song", 330, "Sir John Suckling"),
    entry("A Ballad upon a Wedding", 332, "Sir John Suckling"),
    entry("Song", 336, "Sir John Suckling"),
    entry("From—Hudibras", 340, "Samuel Butler", "Poetry"),

    entry("Wishes, to His Supposed Mistress", 357, "Richard Crashaw"),
    entry("A Hymn to the Name and Honor of the Admirable Saint Teresa", 361, "Richard Crashaw"),
    entry("From—The Flaming Heart", 367, "Richard Crashaw"),
    entry("Charitas Nimia; or, The Dear Bargain", 368, "Richard Crashaw"),
    entry("In the Holy Nativity of Our Lord God", 370, "Richard Crashaw"),
    entry("To the Noblest and Best of Ladies, the Countess of Denbigh", 374, "Richard Crashaw"),

    entry("An Elegy on Ben Jonson", 379, "John Cleveland"),
    entry("Fuscara; or, The Bee Errant", 379, "John Cleveland"),
    entry("Upon Phillis Walking in a Morning before Sun-rising", 382, "John Cleveland"),
    entry("Mark Antony", 383, "John Cleveland"),
    entry("The Rebel Scot", 385, "John Cleveland"),
    entry("Cooper's Hill", 391, "Sir John Denham"),

    entry("To Althea, from Prison", 405, "Richard Lovelace"),
    entry("To Lucasta, Going to the Wars", 406, "Richard Lovelace"),
    entry("To Lucasta, Going beyond the Seas", 407, "Richard Lovelace"),
    entry("Gratiana Dancing and Singing", 408, "Richard Lovelace"),
    entry("The Scrutiny", 408, "Richard Lovelace"),
    entry("The Grasshopper", 409, "Richard Lovelace"),

    entry("The Wish", 415, "Abraham Cowley"),
    entry("To the Royal Society", 417, "Abraham Cowley"),
    entry("Hymn to Light", 423, "Abraham Cowley"),
    entry("On the Death of Mr. Crashaw", 427, "Abraham Cowley"),
    entry("On the Death of Mr. William Hervey", 429, "Abraham Cowley"),
    entry("Anacreontics: Drinking", 434, "Abraham Cowley"),
    entry("Anacreontics: The Epicure", 434, "Abraham Cowley"),
    entry("Anacreontics: The Grasshopper", 435, "Abraham Cowley"),
    entry("The Praise of Pindar", 436, "Abraham Cowley"),
    entry("Of Solitude", 438, "Abraham Cowley"),

    entry("The Garden", 444, "Andrew Marvell"),
    entry("The Nymph Complaining for the Death of Her Fawn", 446, "Andrew Marvell"),
    entry("The Picture of Little T. C. in a Prospect of Flowers", 450, "Andrew Marvell"),
    entry("The Mower to the Glowworms", 451, "Andrew Marvell"),
    entry("The Mower's Song", 452, "Andrew Marvell"),
    entry("The Definition of Love", 453, "Andrew Marvell"),
    entry("To His Coy Mistress", 454, "Andrew Marvell"),
    entry("Bermudas", 456, "Andrew Marvell"),
    entry("An Horatian Ode", 457, "Andrew Marvell"),

    entry("The Retreat", 464, "Henry Vaughan"),
    entry("Metrum V", 465, "Henry Vaughan"),
    entry("Childhood", 466, "Henry Vaughan"),
    entry("Corruption", 467, "Henry Vaughan"),
    entry("Man", 468, "Henry Vaughan"),
    entry("[The Hidden Flower]", 469, "Henry Vaughan"),
    entry("Love and Discipline", 471, "Henry Vaughan"),
    entry("The Bird", 472, "Henry Vaughan"),
    entry("Cock-crowing", 473, "Henry Vaughan"),
    entry("The Timber", 475, "Henry Vaughan"),
    entry("The Waterfall", 477, "Henry Vaughan"),
    entry("Unprofitableness", 478, "Henry Vaughan"),
    entry("Vanity of Spirit", 479, "Henry Vaughan"),
    entry("The Night", 480, "Henry Vaughan"),
    entry("The World", 482, "Henry Vaughan"),
    entry("[Departed Friends]", 483, "Henry Vaughan"),
    entry("Peace", 485, "Henry Vaughan"),
    entry("The Book", 485, "Henry Vaughan"),

    entry("Absalom and Achitophel", 490, "John Dryden", "Poetry"),
    entry("To Mrs. Anne Killigrew", 520, "John Dryden"),
    entry("Alexander's Feast", 526, "John Dryden"),

    entry("Wonder", 536, "Thomas Traherne"),
    entry("Innocence", 538, "Thomas Traherne"),
    entry("On News", 540, "Thomas Traherne"),
    entry("The Salutation", 542, "Thomas Traherne"),
    entry("Desire", 543, "Thomas Traherne"),
    entry("The Choice", 545, "Thomas Traherne"),
    entry("The Recovery", 547, "Thomas Traherne"),

    entry("Upon Drinking in a Bowl", 552, "John Wilmot"),
    entry("The Mistress. A Song", 553, "John Wilmot"),
    entry("A Song", 554, "John Wilmot"),
    entry("Love and Life. A Song", 555, "John Wilmot"),
    entry("A Song", 555, "John Wilmot"),
    entry("The Answer", 556, "John Wilmot"),
    entry("Constancy. A Song", 557, "John Wilmot"),

    entry("Appendix A: General Bibliography", 558, None, "Reference"),
    entry("Appendix B: Bibliography of Authors", 563, None, "Reference"),
    entry("Index", 571, None, "Index"),
]


def main():
    BACKUP.parent.mkdir(parents=True, exist_ok=True)
    if not BACKUP.exists():
        shutil.copy2(app.DB_PATH, BACKUP)

    with app.connect() as db:
        payload = app.get_item(db, ITEM_ID)
        if not payload or payload["title"] != "English Poetry":
            raise RuntimeError("Expected item 171 to be the existing English Poetry record")
        payload["contents"] = contents
        app.save_item(payload, ITEM_ID)

    print(f"Indexed {len(contents)} contents in item {ITEM_ID}.")
    print(f"Backup: {BACKUP}")


if __name__ == "__main__":
    main()
