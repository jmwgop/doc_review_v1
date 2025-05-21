# client_code/MainReviewForm/json_renderer.py
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
    # List of dicts (table-like structure)
    if value and isinstance(value[0], dict):
      flat_rows = [flatten_dict(row) for row in value]
      keys = sorted({k for row in flat_rows for k in row})
      total_width = len(keys) * 16  # 16em per column

      # --- NEW: scroll wrapper -------------------------------------------------
      # --- scroll wrapper stays ---
      # scrollable wrapper
      scroll_wrapper = FlowPanel(role="table-scroll", width="100%")

      table_container = ColumnPanel()        # no fixed width

      # ─── Header ───────────────────────────────────────────────────────────────
      header_row = FlowPanel(spacing_above="none", spacing_below="none")
      for key in keys:
        header_row.add_component(
          Label(text=key.capitalize().replace('_', ' '),
                bold=True, underline=True,
                spacing_above="none", spacing_below="none")   # ← no width
        )
      table_container.add_component(header_row)

      # ─── Data rows ────────────────────────────────────────────────────────────
      for row in flat_rows:
        data_row = FlowPanel(spacing_above="none", spacing_below="none")
        for key in keys:
          cell = row.get(key, "")
          widget_cls = TextArea if (isinstance(cell, str) and (len(cell) > 80 or '\n' in cell)) else TextBox
          data_row.add_component(
            widget_cls(text=str(cell) if cell is not None else "",
                       spacing_above="none", spacing_below="none")   # ← no width
          )
        table_container.add_component(data_row)

      # assemble
      scroll_wrapper.add_component(table_container)
      container.add_component(scroll_wrapper)

    else:
      for item in value:
        render_json(item, container)
    return

  # Fallback
  container.add_component(Label(text=f"(Unrenderable: {repr(value)})"))
