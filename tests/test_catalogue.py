import csv
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import app


class CatalogueTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_path = app.DB_PATH
        self.original_pages_dir = app.PAGES_DIR
        app.DB_PATH = Path(self.temp_dir.name) / "test.sqlite3"
        app.PAGES_DIR = Path(self.temp_dir.name) / "docs"
        app.init_db()

    def tearDown(self):
        app.DB_PATH = self.original_path
        app.PAGES_DIR = self.original_pages_dir
        self.temp_dir.cleanup()

    def test_anthology_content_is_searchable_and_resolves_to_item(self):
        item_id = app.save_item({
            "title": "The Oxford Book of American Verse",
            "media_category": "Book",
            "item_type": "Anthology",
            "stack": "2",
            "shelf_row": "4",
            "contributors": [{"name": "F. O. Matthiessen", "role": "Editor"}],
            "contents": [{
                "title": "Because I could not stop for Death",
                "work_type": "Poem",
                "page_start": "301",
                "contributors": [{"name": "Emily Dickinson", "role": "Author"}],
            }],
        })

        results = app.search_items("because death")

        self.assertEqual([item_id], [result["id"] for result in results])
        self.assertEqual("Stack 2, Row 4", results[0]["location"])
        self.assertEqual("Because I could not stop for Death", results[0]["matched_contents"][0]["title"])
        with app.connect() as db:
            record = app.get_item(db, item_id)
        self.assertEqual("Because I could not stop for Death", record["contents"][0]["title"])
        self.assertEqual("Emily Dickinson", record["contents"][0]["contributors"][0]["name"])

    def test_item_can_be_edited_without_leaving_orphan_works(self):
        item_id = app.save_item({"title": "First title", "contents": [{"title": "Old essay"}]})
        app.save_item({"title": "Revised title", "contents": [{"title": "New essay"}]}, item_id)

        self.assertEqual([], app.search_items("Old essay"))
        self.assertEqual(item_id, app.search_items("New essay")[0]["id"])
        with app.connect() as db:
            self.assertEqual(1, db.execute("SELECT count(*) FROM works").fetchone()[0])

    def test_set_volume_and_flexible_metadata_round_trip(self):
        item_id = app.save_item({
            "title": "Collected Scores",
            "media_category": "Sheet music",
            "set_name": "Piano Works",
            "volume_number": 3,
            "metadata": {"binding": "cloth", "condition": "annotated"},
        })
        with app.connect() as db:
            record = app.get_item(db, item_id)

        self.assertEqual("Piano Works", record["set_name"])
        self.assertEqual(3, record["volume_number"])
        self.assertEqual("cloth", record["metadata"]["binding"])

    def test_csv_anthology_rows_are_grouped(self):
        stream = io.StringIO()
        writer = csv.DictWriter(stream, fieldnames=[
            "record_key", "title", "media_category", "contributors", "content_title", "content_contributors"
        ])
        writer.writeheader()
        writer.writerow({
            "record_key": "anth-1", "title": "Essays Annual", "media_category": "Book",
            "contributors": "Editor: Alex Reader", "content_title": "First Essay",
            "content_contributors": "Author: Casey Writer",
        })
        writer.writerow({
            "record_key": "anth-1", "title": "Essays Annual", "media_category": "Book",
            "contributors": "Editor: Alex Reader", "content_title": "Second Essay",
            "content_contributors": "Author: Morgan Writer",
        })

        records = app.parse_import({"format": "csv", "content": stream.getvalue()})

        self.assertEqual(1, len(records))
        self.assertEqual(2, len(records[0]["contents"]))
        self.assertEqual("Alex Reader", records[0]["contributors"][0]["name"])

    def test_json_export_is_reimportable(self):
        app.save_item({
            "title": "One Story",
            "metadata": {"provenance": "gift"},
            "digital_files": [{"label": "Scan", "relative_path": "one-story/scan.pdf"}],
        })
        exported = app.export_records()
        valid, errors = app.validate_import(json.loads(json.dumps(exported)))

        self.assertEqual(1, len(valid))
        self.assertEqual([], errors)
        self.assertEqual("one-story/scan.pdf", exported[0]["digital_files"][0]["relative_path"])

    def test_digital_files_are_searchable_and_paths_are_safe(self):
        item_id = app.save_item({
            "title": "Old Book",
            "digital_files": [{"label": "Preservation scan", "relative_path": "old-books/old-book.pdf"}],
        })

        self.assertEqual(item_id, app.search_items("preservation")[0]["id"])
        with self.assertRaisesRegex(ValueError, "inside digital_library"):
            app.save_item({"title": "Unsafe", "digital_files": [{"relative_path": "../private.pdf"}]})

    def test_isbn_validation_accepts_ten_and_thirteen_digit_formats(self):
        self.assertEqual("0140328726", app.normalize_isbn("0-14-032872-6"))
        self.assertEqual("9780140328721", app.normalize_isbn("978-0-14-032872-1"))
        with self.assertRaisesRegex(ValueError, "check digit"):
            app.normalize_isbn("9780140328722")

    def test_open_library_response_is_mapped_to_catalogue_fields(self):
        result = app.transform_open_library("9780140328721", {
            "title": "Fantastic Mr. Fox",
            "publish_date": "1988",
            "publishers": [{"name": "Puffin"}],
            "authors": [{"name": "Roald Dahl"}],
            "languages": [{"key": "/languages/eng"}],
            "number_of_pages": 96,
        })

        self.assertEqual("Fantastic Mr. Fox", result["fields"]["title"])
        self.assertEqual("Puffin", result["fields"]["publisher"])
        self.assertEqual("English", result["fields"]["language"])
        self.assertEqual("Roald Dahl", result["contributors"][0]["name"])
        self.assertEqual(96, result["additional"]["Number of pages"])

    def test_isbn_results_are_cached_locally(self):
        fetched = {
            "isbn": "9780140328721", "source": "Open Library", "source_url": "https://openlibrary.org/",
            "fields": {"title": "Fantastic Mr. Fox"}, "contributors": [], "additional": {},
        }
        with patch("app.fetch_open_library", return_value=fetched) as fetch:
            first = app.lookup_isbn("9780140328721")
            second = app.lookup_isbn("9780140328721")

        self.assertFalse(first["cached"])
        self.assertTrue(second["cached"])
        fetch.assert_called_once_with("9780140328721")

    def test_public_export_uses_an_explicit_allowlist(self):
        app.save_item({
            "title": "Public Book",
            "publisher": "Public Press",
            "stack": "3",
            "shelf_row": "2",
            "shelf_position": "Right side",
            "notes": "private item note",
            "metadata": {"price_paid": "$45", "provenance": "private"},
            "digital_files": [{"label": "Private scan", "relative_path": "private/public-book.pdf", "notes": "private file note"}],
            "contributors": [{"name": "Visible Author", "role": "Author"}],
            "contents": [{
                "title": "Visible Essay", "page_start": "12", "notes": "private content note",
                "metadata": {"private": "value"},
            }],
        })

        record = app.public_export_records()[0]
        serialized = json.dumps(record)

        self.assertEqual("Stack 3, Row 2", ", ".join([f"Stack {record['stack']}", f"Row {record['shelf_row']}"]))
        self.assertEqual("Right side", record["shelf_position"])
        self.assertEqual("Visible Author", record["contributors"][0]["name"])
        self.assertEqual("12", record["contents"][0]["page_start"])
        for forbidden in ("notes", "metadata", "digital_files", "relative_path", "private scan", "private file note", "created_at", "updated_at", "private item note", "$45", "private content note"):
            self.assertNotIn(forbidden, serialized)

        result = app.build_public_site()
        generated = json.loads((app.PAGES_DIR / "catalogue.json").read_text())
        self.assertEqual(1, result["items"])
        self.assertEqual(record, generated["items"][0])
        self.assertTrue((app.PAGES_DIR / "index.html").is_file())
        self.assertTrue((app.PAGES_DIR / ".nojekyll").is_file())


if __name__ == "__main__":
    unittest.main()
