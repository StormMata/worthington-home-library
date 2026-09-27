# Public catalogue data policy

The public GitHub Pages site is generated from an explicit allowlist. Adding a new private database field does **not** make it public automatically.

## Published

- Bibliographic description: title, subtitle, category, record type, publication date, publisher, edition, public identifier, language, and description
- Contributors: names and roles
- Collection structure: set name, volume label, and volume number
- Indexed contents: title, type, publication date, language, contributor names and roles, sequence, and page range
- Physical location: stack, row, and shelf-position note

## Never published

- Item or contained-work notes
- All custom metadata
- Internal database IDs
- Creation and modification timestamps
- ISBN lookup cache and fetch timestamps
- Import previews or source files
- Backups or the SQLite database
- Digital files, file paths, and private file notes
- Editing, deletion, lookup, import, export, or backup endpoints

The enforced field lists are `PUBLIC_ITEM_FIELDS` and `PUBLIC_CONTENT_FIELDS` in `app.py`. Automated tests fail if excluded sample data reaches the public export.
