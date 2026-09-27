# Digital library

Store local scans and other digital media in this directory. Subdirectories are encouraged; for example:

```text
digital_library/author-name/book-title.pdf
```

In a catalogue record, enter only the relative part (`author-name/book-title.pdf`). The local application will provide an **Open file** link when that file exists.

Files placed here are intentionally ignored by Git and are never included in the public GitHub Pages catalogue. They are also not embedded in SQLite backups, so back up this directory separately.
