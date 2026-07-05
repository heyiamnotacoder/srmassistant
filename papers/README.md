# papers/

Drop the PDFs for the current review batch here. One extraction agent is spawned per PDF.

- Use descriptive filenames (e.g., `smith_2023.pdf`) — the extraction output is named `extractions/<filename>.json`.
- Scanned PDFs are fine; pages are read visually, no OCR preprocessing needed.
- Adding papers mid-review is fine: re-run `/srma-extract` and only new papers are extracted.
