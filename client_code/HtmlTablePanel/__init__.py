from ._anvil_designer import HtmlTablePanelTemplate
from anvil import *
import anvil.server
import anvil.js                     # NEW – lets us run JS from Python
from ..MainReviewForm import json_renderer   # NEW – for the helper JS

class HtmlTablePanel(HtmlTablePanelTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)
    self._html = ""

  @property
  def html(self):
    return self._html

  @html.setter
  def html(self, value):
    self._html = value
    self.clear()
    self.add_component(HtmlTemplate(html=value))

  # ---------- NEW ----------
  def get_table_data(self):
    """
    Called by json_renderer.extract_edited_data().
    Returns a dict of all <input>/<textarea> values that carry
    data-tags starting with 'table_'.
    """
    # Inject the JS helper once per browser session
    if not hasattr(anvil.js.window, "getTableData"):
      anvil.js.window.eval(json_renderer.get_table_data_js())
    # Run the helper and hand its result back to Python
    return anvil.js.call_js("getTableData")
