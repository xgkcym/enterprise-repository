# Chinese Documents Seed

This folder contains a curated seed set of Chinese-language financial documents in `pdf` format.

Why `pdf`:
- The project has first-class loaders and chunkers for `pdf`, `doc/docx`, `md/markdown`, `txt`, `xls/xlsx`, `csv`, `pptx`, `json`, and common image formats.
- `pdf` is the safest choice here because the ingestion path is already implemented and works well for report-style documents.

Source profile:
- Public disclosures from CNINFO (`static.cninfo.com.cn`)
- Chinese-language insurance and financial reporting documents
- Verified after download to ensure the saved payload starts with the PDF file header

Manifest:
- See `manifest.csv` in this folder for the document list and original source URLs.
