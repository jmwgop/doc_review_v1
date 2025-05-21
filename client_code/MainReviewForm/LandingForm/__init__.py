from ._anvil_designer import LandingFormTemplate
from anvil import *
import anvil.server
from ..ReviewForm import ReviewForm

class LandingForm(LandingFormTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)

    # Clear the status text
    self.doc_status.text = ""

    # Populate the dropdown from the server
    try:
      items = anvil.server.call('get_document_dropdown_items')
      self.doc_dropdown.items = items
      self.doc_dropdown.selected_value = None
      if not items or (len(items) == 1 and not items[0][1]):
        self.doc_status.text = "No documents found."
      else:
        self.doc_status.text = "Select a document to review and press Load Document."
    except Exception as e:
      self.doc_status.text = f"Error loading documents: {e}"

  def load_btn_click(self, **event_args):
    doc_id = self.doc_dropdown.selected_value
    if doc_id:
      self.doc_status.text = "Loading document..."
      open_form(ReviewForm(doc_id=doc_id))
    else:
      self.doc_status.text = "Please select a document before loading."
