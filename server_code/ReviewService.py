import anvil.server
import anvil.tables as tables
from anvil.tables import app_tables
import json

@anvil.server.callable
def get_document_dropdown_items():
  """
    Returns a list of (label, value) tuples for the dropdown.
    """
  docs = app_tables.documents.search()
  return [(d["doc_id"], d["doc_id"]) for d in docs]

@anvil.server.callable
def get_document(doc_id):
  """
    Returns (pdf_inline_url, result_json, flags) for a given doc_id.
    pdf_inline_url: the inline URL to the PDF media (or None)
    result_json: the JSON dict from the result_json column (or {})
    flags: the flags dict from the flags column (or {})
    """
  row = app_tables.documents.get(doc_id=doc_id)
  if not row:
    raise Exception(f"Document with id '{doc_id}' not found.")

    # Get PDF URL
  pdf_media = row["pdf"]
  pdf_url = pdf_media.get_url(False) if pdf_media else None

  # Get JSON result
  result_json = row["result_json"] or {}

  # Get flags
  flags = row["flags"] or {}

  return pdf_url, result_json, flags
