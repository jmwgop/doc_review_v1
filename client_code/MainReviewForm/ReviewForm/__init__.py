from ._anvil_designer import ReviewFormTemplate
from anvil import *
import anvil.server
from .. import json_renderer

class ReviewForm(ReviewFormTemplate):
  def __init__(self, doc_id=None, **properties):
    self.init_components(**properties)
    self.doc_id = doc_id

    # --- Set widths so they display SIDE BY SIDE and scroll works ---
    self.pdf_frame.width = "600px"         # PDF area
    self.pdf_frame.height = "100vh"        # Tall PDF
    self.pdf_frame.role = "pdf-sticky"     # Optional role for custom styles

    self.json_container.width = "1400px"   # Wide enough for tables and scroll
    self.json_container.wrap_on = "never"  # Don't wrap child components

    # If you want, you can add a role for targeted table CSS:
    # self.json_container.role = "json-table-parent"

    if self.doc_id:
      self.load_document(self.doc_id)

  def load_document(self, doc_id):
    try:
      pdf_url, result_json, flags = anvil.server.call('get_document', doc_id)
    except Exception as e:
      alert(f"Error loading document: {e}")
      return

    self.pdf_frame.url = pdf_url if pdf_url else "about:blank"
    self.json_container.clear()

    # Get the main JSON payload
    if "output" in result_json and isinstance(result_json["output"], list) and result_json["output"]:
      payload = result_json["output"][0]
    else:
      alert("No data found in JSON output.")
      return

    # Render the JSON as editable Anvil components (tables, etc.)
    json_renderer.render_json(payload, self.json_container)
