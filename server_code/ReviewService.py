import anvil.server
import anvil.tables as tables
from anvil.tables import app_tables

@anvil.server.callable
def get_document_dropdown_items():
  """
    Returns a list of (label, value) tuples for the dropdown.
    """
  docs = app_tables.documents.search()
  # Use doc_id for both label and value; you could add more here if you want
  return [(d["doc_id"], d["doc_id"]) for d in docs]
