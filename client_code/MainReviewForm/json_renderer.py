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

def render_json(value, container, label=None, _level=0):
  """
    Recursively renders JSON into an Anvil container as editable inputs.
    Args:
        value: The JSON data (dict, list, or scalar)
        container: The Anvil container (ColumnPanel, etc.) to add components to
        label: Optional label for this section
        _level: (internal) indent level for debug prints
    """
  # Only print what matters for layout debug
  if label is not None:
    print(f"[RENDER] Section label: {label}")

    # 1. Scalars (str, int, float, bool, None)
  if isinstance(value, (str, int, float, bool)) or value is None:
    # Don't spam prints for scalars
    vstr = "" if value is None else str(value)
    if isinstance(value, str) and (len(value) > 80 or '\n' in value):
      container.add_component(TextArea(text=vstr))
    else:
      container.add_component(TextBox(text=vstr))
    return

    # 2. Dicts
  if isinstance(value, dict):
    for k, v in value.items():
      render_json(v, container, label=k, _level=_level+1)
    return

    # 3. Lists
  if isinstance(value, list):
    if value and isinstance(value[0], dict):
      # ----------- Render list of dicts as a table with horizontal scroll -----------
      flat_rows = [flatten_dict(row) for row in value]
      keys = sorted({k for row in flat_rows for k in row})

      # Header row
      header_row = FlowPanel(role='horizontal-scroll')
      for key in keys:
        header_row.add_component(
          Label(
            text=key.capitalize().replace('_', ' '),
            bold=True,
            underline=True,
            width="12em"
          )
        )
      print("[DEBUG] Rendered header row with horizontal-scroll role.")
      container.add_component(header_row)

      # Data rows
      for i, row in enumerate(flat_rows):
        data_row = FlowPanel(role='horizontal-scroll')
        for key in keys:
          cell = row.get(key, "")
          widget_cls = TextArea if (isinstance(cell, str) and (len(cell) > 80 or '\n' in cell)) else TextBox
          data_row.add_component(
            widget_cls(
              text=str(cell) if cell is not None else "",
              width="12em"
            )
          )
        print(f"[DEBUG] Rendered data row {i} with horizontal-scroll role.")
        container.add_component(data_row)
      return
    else:
      for idx, item in enumerate(value):
        render_json(item, container, _level=_level+1)
      return

    # Fallback for anything else
  print("[DEBUG] Unrenderable value encountered, type:", type(value).__name__)
  container.add_component(Label(text=f"(Unrenderable: {repr(value)})"))
