# Shelf Index

Shelf Index is a private, local catalogue for a physical media library. It runs on your computer, stores everything in SQLite, and does not need an internet connection.

## Start it

On macOS, double-click **`run.command`**. Your browser opens to:

```text
http://127.0.0.1:8765
```

You can also start it from Terminal:

```sh
python3 app.py
```

Press Control-C in the Terminal window to stop it. Python 3.10 or newer is the only requirement; the application has no third-party packages.

## Your data

The working database is created at:

```text
data/catalogue.sqlite3
```

The database uses SQLite's write-ahead log while Shelf Index is running. For a complete backup, use **Import & backup → Download SQLite backup** inside the application, or stop Shelf Index before copying the entire `data` folder.

The JSON export is human-readable and can be imported into a fresh copy of Shelf Index. Keep periodic backups somewhere outside this folder, such as an external drive.

## Catalogue structure

- A **physical item** is the book, score, magazine, disc set, or other object on your shelf.
- A **contained work** is a poem, story, essay, composition, or other searchable piece inside it.
- Contributors can have roles such as Author, Editor, Translator, Composer, or Illustrator.
- Set name, volume number, stack, row, and an optional position describe how an item belongs and where it lives.
- Custom fields hold metadata that does not fit the standard fields.

Searching for a contained work or its contributor returns the physical item and shelf location needed to retrieve it.

## ISBN lookup

In the item editor, enter an ISBN-10 or ISBN-13 and select **Look up**. Shelf Index validates the check digit, requests edition metadata from Open Library, and displays a field-by-field comparison. Existing values are never replaced automatically: select the differences you want and use **Apply selected fields**, then save the item normally.

ISBN lookup is the only feature that requires an internet connection. Successful responses are cached in the local database, while every other catalogue feature remains available offline.

## Batch imports

Open **Import & backup** and choose a `.json` or `.csv` file. Shelf Index validates and previews the file before anything is added.

Starter files are available in [`samples/import-template.json`](samples/import-template.json) and [`samples/import-template.csv`](samples/import-template.csv).

For CSV anthologies, give every row for the same physical volume the same `record_key`. Each row can then contain one `content_title`. Contributor cells use this format:

```text
Author: Ursula Le Guin; Editor: Robert Silverberg
```

Any CSV column beginning with `meta_` becomes a custom field—for example, `meta_condition` creates a `condition` field.

## Run the checks

```sh
python3 -m unittest discover -s tests -v
```

## Public read-only catalogue

Shelf Index can generate a separate static site for GitHub Pages. The public site contains only an explicit allowlist:

- Titles, subtitles, media categories, and record types
- Authors, editors, and other contributor names and roles
- Publication dates, publishers, editions, identifiers, languages, and descriptions
- Sets and volume information
- Contained-work titles, contributors, types, dates, languages, sequence, and page ranges
- Stack, row, and shelf-position location

It always excludes private notes, custom metadata, internal database IDs, timestamps, import and backup tools, ISBN lookup caches, and every editing or deletion capability. The SQLite database is excluded from Git by [`.gitignore`](.gitignore).

Generate the public site with **Import & backup → Prepare public catalogue** in the local application, or double-click **`publish.command`**. The generated files appear in `docs/` and contain no server-side code.

### One-time GitHub Pages setup

1. Create an empty public repository on GitHub. A public repository allows GitHub Pages on the free GitHub plan.
2. Commit this project and push its `main` branch to that repository. Only `docs/catalogue.json` contains public catalogue data; `data/` remains local and ignored.
3. In the GitHub repository, open **Settings → Pages** and set **Source** to **GitHub Actions**.
4. The included `.github/workflows/pages.yml` workflow publishes the `docs/` folder. Its completed run displays the public URL.

For later updates, regenerate the public site, review the changes to `docs/catalogue.json`, and commit and push them. Nothing is published until you choose to push it.
