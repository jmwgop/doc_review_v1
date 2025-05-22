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
    # load helper JS once
    if not hasattr(anvil.js.window, "getTableData"):
      anvil.js.window.eval(json_renderer.get_table_data_js())
  
    nested = anvil.js.call_js("getTableData")  # {"tracts":[…], "parties":[…]}
    flat = {}
  
    # turn it into  {"table_tracts_0_description": "...", ...}
    for tbl, rows in (nested or {}).items():
      if rows:
        for idx, row in enumerate(rows):
          if row:
            for col, val in row.items():
              flat[f"table_{tbl}_{idx}_{col}"] = val
    return flat

