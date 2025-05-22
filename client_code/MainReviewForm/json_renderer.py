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
      render_json(v, container, label=k, _level=_level+1)
    return

    # 3. Lists
  if isinstance(value, list):
    if value and isinstance(value[0], dict):
      # ----------- Render as a proper horizontally scrollable table -----------
      flat_rows = [flatten_dict(row) for row in value]
      keys = sorted({k for row in flat_rows for k in row})

      # Max width for the table container
      max_width = "1500px"  # <-- Change this value if you want a different max width

      # Minimum width for the table itself, based on columns
      table_width = len(keys) * 12 + 2  # 12em per column + 2em padding
      min_width_em = 8
      max_width_em = 20
      
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
                display: table;
                border-collapse: collapse;
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
                  text-align: left;
                  white-space: normal;
                  word-wrap: break-word;
                ">{key.capitalize().replace('_', ' ')}</div>
                '''
      table_html += '</div>'

      # Data rows
      for i, row in enumerate(flat_rows):
        bg_color = "#ffffff" if i % 2 == 0 else "#f9f9f9"
        table_html += f'<div style="display: table-row; background-color: {bg_color};">'
        for key in keys:
          cell = row.get(key, "")
          cell_text = str(cell) if cell is not None else ""
          # Escape HTML in cell content
          cell_text = cell_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
          table_html += f'''
                    <div style="
                      display: table-cell;
                      min-width: {min_width_em}em;
                      max-width: {max_width_em}em;
                      width: auto;
                      padding: 8px;
                      border: 1px solid #ddd;
                      text-align: left;
                      white-space: normal;
                      word-wrap: break-word;
                      overflow: hidden;
                      text-overflow: ellipsis;
                    ">{cell_text}</div>
                    '''
        table_html += '</div>'

      table_html += '</div></div>'

      # Add the table to the container
      container.add_component(Label(text=f"Table: {len(flat_rows)} rows"))
      container.add_component(Spacer(height=5))
      table_panel = HtmlTablePanel()
      table_panel.html = table_html
      container.add_component(table_panel)
      container.add_component(Spacer(height=10))

      print(f"[DEBUG] Rendered HTML table with {len(flat_rows)} rows and {len(keys)} columns")
      return
    else:
      for idx, item in enumerate(value):
        render_json(item, container, _level=_level+1)
      return

    # Fallback for anything else
  print("[DEBUG] Unrenderable value encountered, type:", type(value).__name__)
  container.add_component(Label(text=f"(Unrenderable: {repr(value)})"))
