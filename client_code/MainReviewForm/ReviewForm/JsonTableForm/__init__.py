from ._anvil_designer import JsonTableFormTemplate
from anvil import *

class JsonTableForm(JsonTableFormTemplate):
  def __init__(self, data_list=None, **properties):
    self.init_components(**properties)
    self.container.clear()
    data_list = data_list or []

    # Get headers from first item (if any)
    keys = list(data_list[0].keys()) if data_list and isinstance(data_list[0], dict) else []

    # Build header row
    if keys:
      header_row = FlowPanel()
      for key in keys:
        header_row.add_component(Label(text=key.capitalize(), bold=True, underline=True, spacing_above='none', spacing_below='none', width="12em"))
      self.container.add_component(header_row)

    # Build data rows
    for row in data_list:
      data_row = FlowPanel()
      for key in keys:
        val = row.get(key, "")
        if isinstance(val, dict):
          val_str = ", ".join(f"{k}: {v}" for k, v in val.items())
        else:
          val_str = str(val)
        data_row.add_component(Label(text=val_str, spacing_above='none', spacing_below='none', width="12em"))
      self.container.add_component(data_row)
