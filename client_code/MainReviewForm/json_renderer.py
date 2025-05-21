# json_renderer.py

from anvil import *

def flatten_dict(d, parent_key='', sep='_'):
  """Flattens a dict, so {'a': {'b': 1}} -> {'a_b': 1}"""
  items = []
  for k, v in d.items():
    new_key = f"{parent_key}{sep}{k}" if parent_key else k
    if isinstance(v, dict):
      items.extend(flatten_dict(v, new_key, sep=sep).items())
    else:
      items.append((new_key, v))
  return dict(items)

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
    vstr = "" if value is None else str(value)
    # Long strings or multiline: textarea, else textbox
    if isinstance(value, str) and (len(value) > 80 or '\n' in value):
      container.add_component(TextArea(text=vstr, width="24em"))
    else:
      container.add_component(TextBox(text=vstr, width="16em"))
    return

    # 2. Dicts
  if isinstance(value, dict):
    for k, v in value.items():
      render_json(v, container, label=k)
    return

    # 3. Lists
  if isinstance(value, list):
    # List of dicts (table-like structure)
    if value and isinstance(value[0], dict):
      # Flatten all rows to get all possible columns
      flat_rows = [flatten_dict(row) for row in value]
      all_keys = set()
      for row in flat_rows:
        all_keys.update(row.keys())
      keys = sorted(all_keys)
      # Outer horizontally scrollable container
      scroll_container = FlowPanel()
    
      scroll_container.role = "table-scroll"
            # Table: Header row
      header_row = FlowPanel()
      for key in keys:
        header_row.add_component(Label(
          text=key.capitalize().replace('_', ' '), bold=True, underline=True, width="16em"))
      scroll_container.add_component(header_row)
      # Table: Data rows
      for row in flat_rows:
        data_row = FlowPanel()
        for key in keys:
          cell = row.get(key, "")
          # Editable cell logic
          if isinstance(cell, str) and (len(cell) > 80 or '\n' in cell):
            data_row.add_component(TextArea(text=cell, width="16em"))
          else:
            data_row.add_component(TextBox(text=str(cell), width="16em"))
        scroll_container.add_component(data_row)
      container.add_component(scroll_container)
    else:
      # List of scalars or empty list
      for item in value:
        render_json(item, container)

    # Fallback: unknown type
  container.add_component(Label(text=f"(Unrenderable: {repr(value)})"))
