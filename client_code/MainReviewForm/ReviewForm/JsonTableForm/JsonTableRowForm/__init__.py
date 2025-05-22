from ._anvil_designer import JsonTableRowFormTemplate
from anvil import *

class JsonTableRowForm(JsonTableRowFormTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)
    self.container.clear()

    if not self.item:
      self.container.add_component(Label(text="(empty row)"))
      return

    for key, val in self.item.items():
      flow = FlowPanel()
      flow.add_component(Label(text=f"{key}:", bold=True))
      val_str = ", ".join(f"{k}: {v}" for k, v in val.items()) if isinstance(val, dict) else str(val)
      if isinstance(val, str) and (len(val) > 80 or '\n' in val):
        input_widget = TextArea(text=val_str, width="100%")
      else:
        input_widget = TextBox(text=val_str, width="100%")
      flow.add_component(input_widget, width="100%")
      self.container.add_component(flow)

    self.container.add_component(Spacer(height=10))
