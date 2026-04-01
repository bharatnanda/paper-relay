# TODO

## Must Do Next

- Show missing-context / weak-extraction indicators more systematically on the paper views.
- Decide whether raw figure/table snapshots should be visually de-emphasized now that interpreted evidence exists.
- Run export tests in an environment with `reportlab`.
- Run parser tests in an environment with `pdfplumber`.
- Rerun end-to-end analysis on real papers after backend/worker rebuild.
- Review output quality across different paper shapes:
  - theory-heavy
  - benchmark-heavy
  - figure-heavy
- Resolve the Rollup optional native dependency issue in the Docker-based `frontend_tools` build flow.
- Improve prompt behavior for papers where figures and tables materially affect the conclusions.
- Add better fallback handling for papers where PDF text extraction is weak.

## Useful Soon

- Add richer paper metadata to the UI:
  - abstract
  - section list
  - arXiv categories
- Add paper deletion from the library UI if needed.
- Add a manual theme override if system-only theming is not enough.
- Review whether summary JSON should be normalized into explicit Pydantic response models instead of plain `dict`.
- Consider storing parser artifacts separately if summary payloads get too large.
- Add API tests for `GET /api/papers/{paper_id}` covering returned `title`, `authors`, `arxiv_id`, and `pdf_url`.

## Later

- Add true figure understanding for:
  - plots
  - diagrams
  - architecture figures
  - image-heavy pages
- Consider extracting figure regions and sending them through a multimodal model.
- Add better table normalization if `pdfplumber` extraction is noisy.
