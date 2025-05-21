from ._anvil_designer import ReviewFormTemplate
from anvil import *
import anvil.server
from .JsonTableForm import JsonTableForm
import json
from .. import json_renderer

class ReviewForm(ReviewFormTemplate):
  def __init__(self, doc_id=None, **properties):
    self.init_components(**properties)

    self.doc_id = doc_id

    if self.doc_id:
      self.load_document(self.doc_id)

  def load_document(self, doc_id):
    try:
      pdf_url, result_json, flags = anvil.server.call('get_document', doc_id)
    except Exception as e:
      alert(f"Error loading document: {e}")
      return

    # Set the PDF URL in the PDF viewer
    self.pdf_frame.url = pdf_url if pdf_url else "about:blank"

    # Clear out the JSON container for new content
    self.json_container.clear()

    # If your schema is like: {'output': [{...}]}
    if "output" in result_json and isinstance(result_json["output"], list) and result_json["output"]:
      payload = result_json["output"][0]
    else:
      alert("No data found in JSON output.")
      return

    # Render everything recursively!
    json_renderer.render_json(payload, self.json_container)
