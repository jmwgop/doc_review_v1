# json_renderer.py

from anvil import *

def render_json(value, container, label=None):
  """
    Recursively renders JSON into an Anvil container as editable inputs.
    Args:
        value: The JSON data (dict, list, or scalar)
        container: The Anvil container (ColumnPanel, etc.) to add components to
        label: Optional label for this section
    """
  if label is not None:
    container.add_component(Label(text=str(label), bold=True, spacing_above="medium"))

    # 1. Scalars (str, int, float, bool, None)
  if isinstance(value, (str, int, float, bool)) or value is None:
    # Use TextArea for long text, TextBox for short
    vstr = "" if value is None else str(value)
    if isinstance(value, str) and (len(value) > 80 or '\n' in value):
      container.add_component(TextArea(text=vstr))
    else:
      container.add_component(TextBox(text=vstr))
    return

    # 2. Dicts
  if isinstance(value, dict):
    for k, v in value.items():
      render_json(v, container, label=k)
    return

    # 3. Lists
  if isinstance(value, list):
    # List of dicts (table)
    if value and isinstance(value[0], dict):
      keys = list(value[0].keys())
      # Header row
      header_row = FlowPanel()
      for key in keys:
        header_row.add_component(Label(text=key.capitalize(), bold=True, underline=True, width="12em"))
      container.add_component(header_row)
      # Data rows
      for row in value:
        data_row = FlowPanel()
        for key in keys:
          cell = row.get(key, "")
          # Nested dict? Recursively render (add label for context)
          if isinstance(cell, dict):
            sub_container = ColumnPanel()
            render_json(cell, sub_container, label=key)
            data_row.add_component(sub_container)
          else:
            val_str = "" if cell is None else str(cell)
            # Editable cell
            if isinstance(cell, str) and (len(cell) > 80 or '\n' in val_str):
              data_row.add_component(TextArea(text=val_str, width="12em"))
            else:
              data_row.add_component(TextBox(text=val_str, width="12em"))
        container.add_component(data_row)
    else:
      # List of scalars or empty list
      for item in value:
        render_json(item, container)
    return

    # Fallback: unknown type
  container.add_component(Label(text=f"(Unrenderable: {repr(value)})"))
