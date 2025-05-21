from ._anvil_designer import JsonTableRowFormTemplate
from anvil import *

class JsonTableRowForm(JsonTableRowFormTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)
    self.container.clear()

    print(f"Row item: {self.item}")  # Confirm it's getting called

    if not self.item:
      self.container.add_component(Label(text="(empty row)"))
      return

    for key, val in self.item.items():
      # Handle nested dicts
      if isinstance(val, dict):
        val_str = ", ".join(f"{k}: {v}" for k, v in val.items())
      else:
        val_str = str(val)

      flow = FlowPanel()
      flow.add_component(Label(text=f"{key}:", bold=True))
      flow.add_component(Label(text=val_str))
      self.container.add_component(flow)

    # This ensures there's vertical space
    self.container.add_component(Spacer(height=10))
