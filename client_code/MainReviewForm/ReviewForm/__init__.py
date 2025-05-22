# client_code/MainReviewForm/ReviewForm/__init__.py

from ._anvil_designer import ReviewFormTemplate
from anvil import *
import anvil.server
from .. import json_renderer


class ReviewForm(ReviewFormTemplate):

  # ──────────────────────────────────────────────────────────────────────
  #  Constructor
  # ──────────────────────────────────────────────────────────────────────
  def __init__(self, doc_id=None, **properties):
    self.init_components(**properties)
    self.doc_id = doc_id

    # PDF-iframe and JSON panel side-by-side
    self.pdf_frame.width  = "600px"
    self.pdf_frame.height = "100vh"
    self.pdf_frame.role   = "pdf-sticky"        # optional CSS anchor
    self.json_container.width   = "1400px"
    self.json_container.wrap_on = "never"

    # ── build the dropdown ────────────────────────────────────────────────
    try:
      items = anvil.server.call('get_document_dropdown_items')  # [(label, value), …]
      # prepend a blank choice so nothing is selected by default
      items_with_blank = [("-- Select a document --", None)] + items
      self.doc_dropdown.items = items_with_blank

      # pre-select if __init__ was given a doc_id
      if doc_id:
        self.doc_dropdown.selected_value = doc_id
      else:
        self.doc_dropdown.selected_value = None

    except Exception as e:
      alert(f"Error loading document list: {e}")

    # load the initial document (if any)
    if self.doc_dropdown.selected_value:
      self.load_document(self.doc_dropdown.selected_value)

    self.doc_dropdown.set_event_handler("change", self.doc_dropdown_change)
    if self.doc_id:
      self.load_document(self.doc_id)

  # ──────────────────────────────────────────────────────────────────────
  #  Document loader
  # ──────────────────────────────────────────────────────────────────────
  def load_document(self, doc_id):
    """Fetch the doc, pick the (hard-coded) schema, render the UI."""
    try:
      pdf_url, result_json, flags = anvil.server.call('get_document', doc_id)
    except Exception as e:
      alert(f"Error loading document: {e}")
      return

    # 1️⃣  show PDF
    self.pdf_frame.url = pdf_url or "about:blank"

    # 2️⃣  clear any previous components
    self.json_container.clear()

    # 3️⃣  extract the payload JSON we care about
    if (
      isinstance(result_json, dict)
      and isinstance(result_json.get("output"), list)
      and result_json["output"]
    ):
      payload = result_json["output"][0]
    else:
      alert("No data found in JSON output.")
      return

    # 4️⃣  pick schema  (hard-coded for now)
    schema_name = "base_lease"

    #    fetch structure + field configs in one call
    try:
      schema_bundle = anvil.server.call('get_full_schema_bundle', schema_name)
    except Exception as e:
      alert(f"Could not load schema bundle '{schema_name}': {e}")
      return

    # 5️⃣  render JSON using the layout-aware renderer
    #
    #    NOTE: render_json() now expects the extra kw-arg `schema_bundle`;
    #    that function must be updated in json_renderer.py accordingly.
    #
    json_renderer.render_json(
      payload,
      self.json_container,
      schema_bundle=schema_bundle      # ← new
    )

  # ──────────────────────────────────────────────────────────────────────
  #  Save button
  # ──────────────────────────────────────────────────────────────────────
  def save_btn_click(self, **event_args):
    """Collect edited fields and save back to the DB."""
    try:
      edited_json = json_renderer.get_final_json(self.json_container)
      anvil.server.call('save_document_update', self.doc_id, edited_json)
      alert("Changes saved successfully.", title="Success")
    except Exception as e:
      alert(f"Error saving changes: {e}", title="Save Failed")

  def doc_dropdown_change(self, **event_args):
    """Reload the viewer when the user picks a different document."""
    new_id = self.doc_dropdown.selected_value
    if new_id and new_id != getattr(self, "doc_id", None):
      self.doc_id = new_id
      self.load_document(new_id)
