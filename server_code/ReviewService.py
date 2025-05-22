import anvil.server
import anvil.tables as tables
from anvil.tables import app_tables
import json


@anvil.server.callable
def get_document_dropdown_items():
  """Return a list of (label, value) tuples for the dropdown."""
  docs = app_tables.documents.search()
  return [(d["doc_id"], d["doc_id"]) for d in docs]


@anvil.server.callable
def get_document(doc_id):
  """Return (pdf_inline_url, result_json, flags) for the requested document.

    pdf_inline_url: Inline URL to the PDF media (or None)
    result_json:    Parsed JSON dict from the result_json column (or {})
    flags:          Flags dict from the flags column (or {})
    """
  row = app_tables.documents.get(doc_id=doc_id)
  if not row:
    raise Exception(f"Document with id '{doc_id}' not found.")

    # PDF media URL (inline = False)
  pdf_media = row["pdf"]
  pdf_url = pdf_media.get_url(False) if pdf_media else None

  # Parsed extraction result
  result_json = row["result_json"] or {}

  # Any flags captured during extraction/QA
  flags = row["flags"] or {}

  return pdf_url, result_json, flags


@anvil.server.callable
def save_document_update(doc_id, corrected_json):
  """Persist reviewer edits back to the `corrected_json` column."""
  row = app_tables.documents.get(doc_id=doc_id)
  if not row:
    raise Exception(f"Document with id '{doc_id}' not found.")

    # Store the corrected JSON exactly as provided
  row["corrected_json"] = corrected_json
  return {"status": "saved"}
