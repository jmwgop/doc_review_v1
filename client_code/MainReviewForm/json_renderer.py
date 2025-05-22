# json_renderer.py

from anvil import *
from ..HtmlTablePanel import HtmlTablePanel  # Make sure this exists as a Custom HTML Form!

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

def collect_fields_by_type(value, parent_key='', scalar_fields=None, table_fields=None):
  """
  Recursively collects all scalar fields and table fields from the entire JSON structure.
  Returns two lists: (scalar_fields, table_fields) with their full paths.
  """
  if scalar_fields is None:
    scalar_fields = []
  if table_fields is None:
    table_fields = []

  if isinstance(value, dict):
    for k, v in value.items():
      new_key = f"{parent_key}.{k}" if parent_key else k

      if isinstance(v, (str, int, float, bool)) or v is None:
        # It's a scalar field
        scalar_fields.append((new_key, v))
      elif isinstance(v, list) and v and isinstance(v[0], dict):
        # It's a table
        table_fields.append((new_key, v))
      elif isinstance(v, dict):
        # Recurse into nested dict
        collect_fields_by_type(v, new_key, scalar_fields, table_fields)
      # Skip other types for now

  return scalar_fields, table_fields

def render_json(value, container, label=None, _level=0):
  """
    Recursively renders JSON into an Anvil container as editable inputs.
    Args:
        value: The JSON data (dict, list, or scalar)
        container: The Anvil container (ColumnPanel, etc.) to add components to
        label: Optional label for this section
        _level: (internal) indent level for debug prints
    """
  if label is not None:
    print(f"[RENDER] Section label: {label}")

    # 1. Scalars (str, int, float, bool, None) - NOW WITH LABELS
  if isinstance(value, (str, int, float, bool)) or value is None:
    # Add field label
    if label:
      container.add_component(Label(
        text=f"{label.replace('_', ' ').replace('.', ' > ').title()}:",
        bold=True
      ))

    vstr = "" if value is None else str(value)
    if isinstance(value, str) and (len(value) > 80 or '\n' in value):
      container.add_component(TextArea(text=vstr))
    else:
      container.add_component(TextBox(text=vstr))
    container.add_component(Spacer(height=5))
    return

    # 2. Dicts - Collect and group ALL fields by type first
  if isinstance(value, dict):
    # Only do the type-based grouping at the top level
    if _level == 0:
      scalar_fields, table_fields = collect_fields_by_type(value)

      # Render ALL scalar fields first
      if scalar_fields:
        for field_path, field_value in scalar_fields:
          render_json(field_value, container, label=field_path, _level=_level+1)

      # Then render ALL tables
      if table_fields:
        container.add_component(Spacer(height=20))

        for table_path, table_value in table_fields:
          render_json(table_value, container, label=table_path, _level=_level+1)
    else:
      # For nested objects, render normally (shouldn't happen much with the new approach)
      for k, v in value.items():
        render_json(v, container, label=k, _level=_level+1)
    return

    # 3. Lists
  if isinstance(value, list):
    if value and isinstance(value[0], dict):
      # ----------- Render as HTML table with editable inputs -----------
      flat_rows = [flatten_dict(row) for row in value]
      keys = sorted({k for row in flat_rows for k in row})

      # Max width for the table container
      max_width = "1500px"
      table_width = max(len(keys) * 12 + 2, 60)  # Minimum 60em width for all tables
      min_width_em = 10  # Increased minimum width per column
      max_width_em = 25  # Increased maximum width per column

      # Build HTML string for the table
      table_html = f"""
            <div style="
              width: 100%;
              max-width: {max_width};
              overflow-x: auto;
              border: 1px solid #ddd;
              border-radius: 4px;
              max-height: 400px;
              overflow-y: auto;
            ">
              <div style="
                min-width: {table_width}em;
                width: 100%;
                display: table;
                border-collapse: collapse;
                table-layout: fixed;
              ">
            """

      # Header row
      table_html += '<div style="display: table-row; background-color: #f5f5f5; font-weight: bold;">'
      for key in keys:
        table_html += f'''
                <div style="
                  display: table-cell;
                  min-width: {min_width_em}em;
                  max-width: {max_width_em}em;
                  width: auto;
                  padding: 8px;
                  border: 1px solid #ddd;
                  text-align: center;
                  vertical-align: middle;
                  white-space: normal;
                  word-wrap: break-word;
                ">{key.capitalize().replace('_', ' ')}</div>
                '''
      table_html += '</div>'

      # Data rows with editable inputs
      for i, row in enumerate(flat_rows):
        bg_color = "#ffffff" if i % 2 == 0 else "#f9f9f9"
        table_html += f'<div style="display: table-row; background-color: {bg_color};">'
        for key in keys:
          cell = row.get(key, "")
          cell_text = str(cell) if cell is not None else ""
          # Escape HTML in cell content for input value
          escaped_text = cell_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')

          # Choose input type based on content length
          if len(cell_text) > 80 or '\n' in cell_text:
            input_element = f'<textarea style="width: 100%; height: 60px; border: none; background: transparent; resize: vertical; font-family: inherit; font-size: inherit; padding: 4px; text-align: center;">{escaped_text}</textarea>'
          else:
            input_element = f'<input type="text" value="{escaped_text}" style="width: 100%; border: none; background: transparent; font-family: inherit; font-size: inherit; padding: 4px; text-align: center;" />'

          table_html += f'''
                    <div style="
                      display: table-cell;
                      min-width: {min_width_em}em;
                      max-width: {max_width_em}em;
                      width: auto;
                      padding: 4px;
                      border: 1px solid #ddd;
                      text-align: center;
                      vertical-align: middle;
                      white-space: normal;
                      word-wrap: break-word;
                    ">{input_element}</div>
                    '''
        table_html += '</div>'

      table_html += '</div></div>'

      # Add the table to the container
      table_name = label.replace('_', ' ').replace('.', ' > ').title() if label else "Table"
      container.add_component(Label(text=f"{table_name}: {len(flat_rows)} rows", bold=True))
      container.add_component(Spacer(height=5))
      table_panel = HtmlTablePanel()
      table_panel.html = table_html
      container.add_component(table_panel)
      container.add_component(Spacer(height=10))

      print(f"[DEBUG] Rendered editable HTML table with {len(flat_rows)} rows and {len(keys)} columns")
      return
    else:
      for idx, item in enumerate(value):
        render_json(item, container, _level=_level+1)
      return

    # Fallback for anything else
  print("[DEBUG] Unrenderable value encountered, type:", type(value).__name__)
  container.add_component(Label(text=f"(Unrenderable: {repr(value)})"))