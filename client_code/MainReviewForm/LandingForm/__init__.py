from ._anvil_designer import LandingFormTemplate
from anvil import *
import anvil.server

class LandingForm(LandingFormTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)

    # Populate the dropdown from the server
    try:
      items = anvil.server.call('get_document_dropdown_items')
    except Exception as e:
      self.doc_status_text.text = f"Error loading documents: {e}"
      items = []

    self.doc_dropdown.items = items
    self.doc_dropdown.selected_value = None  # No doc selected initially

  def load_btn_click(self, **event_args):
    doc_id = self.doc_dropdown.selected_value
    if doc_id:
      # Swap to ReviewForm, passing doc_id
      open_form('ReviewForm', doc_id=doc_id)
    else:
      self.doc_status_text.text = "Please select a document before loading."
