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
      field = TextArea(text=vstr, width="100%")
    else:
      field = TextBox(text=vstr, width="100%")

    # Add tag for data extraction
    field.tag = f"field_{label}"
    container.add_component(field)
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

      # Analyze content to determine column widths
      col_widths = {}
      for key in keys:
        max_len = len(key) * 10  # Header length as baseline
        for row in flat_rows:
          cell_text = str(row.get(key, ""))
          # Check if this is "long" content
          if len(cell_text) > 80 or '\n' in cell_text:
            max_len = max(max_len, 280)  # Wide column for long content
          else:
            max_len = max(max_len, min(len(cell_text) * 8 + 20, 200))
        col_widths[key] = max(max_len, 120)  # Minimum 120px

      # Calculate total width
      total_width = sum(col_widths.values()) + 50

      # If we have few columns, use more space
      if len(keys) <= 3:
        min_table_width = "100%"
        table_layout = "auto"
        for key in keys:
          col_widths[key] = max(col_widths[key], 250)  # Bigger minimum for few columns
      else:
        min_table_width = f"{total_width}px"
        table_layout = "fixed"

      # Build HTML string for the table
      table_html = f"""
      <style>
        .json-table-container {{
          width: 100%;
          overflow-x: auto;
          overflow-y: auto;
          max-height: 400px;
          border: 1px solid #ddd;
          border-radius: 4px;
          background: #faf9fa;
          margin-bottom: 10px;
        }}
        .json-table {{
          width: 100%;
          min-width: {min_table_width};
          border-collapse: collapse;
          table-layout: {table_layout};
        }}
        .json-table th {{
          background-color: #f5f5f5;
          font-weight: bold;
          position: sticky;
          top: 0;
          z-index: 10;
          padding: 8px;
          border: 1px solid #ddd;
          text-align: center;
          vertical-align: middle;
        }}
        .json-table td {{
          padding: 8px;
          border: 1px solid #ddd;
          text-align: center;
          vertical-align: middle;
        }}
      """

      # Add specific column widths
      for idx, key in enumerate(keys):
        table_html += f"""
        .json-table th:nth-child({idx + 1}),
        .json-table td:nth-child({idx + 1}) {{
          width: {col_widths[key]}px;
          min-width: {col_widths[key]}px;
        }}
        """

      table_html += """
        .json-table tr:nth-child(even) {
          background-color: #f9f9f9;
        }
        .json-table input[type="text"], .json-table textarea {
          width: calc(100% - 8px);
          border: 1px solid #e0e0e0;
          background: white;
          font-family: inherit;
          font-size: inherit;
          padding: 4px;
          margin: 0;
          text-align: left;
        }
        .json-table textarea {
          height: 60px;
          resize: vertical;
        }
      </style>
      <div class="json-table-container">
        <table class="json-table">
      """

      # Header row
      table_html += '<thead><tr>'
      for key in keys:
        display_name = key.capitalize().replace('_', ' ')
        table_html += f'<th>{display_name}</th>'
      table_html += '</tr></thead>'

      # Data rows with editable inputs
      table_html += '<tbody>'
      for i, row in enumerate(flat_rows):
        table_html += '<tr>'
        for key in keys:
          cell = row.get(key, "")
          cell_text = str(cell) if cell is not None else ""
          # Escape HTML in cell content for input value
          escaped_text = cell_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')

          # Choose input type based on content length
          if len(cell_text) > 80 or '\n' in cell_text:
            input_element = f'<textarea data-tag="table_{label}_{i}_{key}">{escaped_text}</textarea>'
          else:
            input_element = f'<input type="text" value="{escaped_text}" data-tag="table_{label}_{i}_{key}" />'

          table_html += f'<td>{input_element}</td>'
        table_html += '</tr>'
      table_html += '</tbody>'

      table_html += '</table></div>'

      # Add the table to the container
      table_name = label.replace('_', ' ').replace('.', ' > ').title() if label else "Table"
      container.add_component(Label(text=f"{table_name}: {len(flat_rows)} rows", bold=True))
      container.add_component(Spacer(height=5))
      table_panel = HtmlTablePanel()
      table_panel.html = table_html
      container.add_component(table_panel)
      container.add_component(Spacer(height=10))

      return
    else:
      for idx, item in enumerate(value):
        render_json(item, container, _level=_level+1)
      return

  # Fallback for anything else
  container.add_component(Label(text=f"(Unrenderable: {repr(value)})"))


# ---------- Data extraction helpers ----------

def extract_edited_data(container):
  """Extract edited data from the form"""
  scalars, tables = {}, {}

  def walk(c):
    # Special handling for HtmlTablePanel
    if hasattr(c, 'get_table_data'):
      # This is our custom HtmlTablePanel with data extraction
      html_data = c.get_table_data()
      for tag_str, value in html_data.items():
        if tag_str and tag_str.startswith('table_'):
          parts = tag_str.split('_', 3)
          if len(parts) >= 4:
            _, tbl, idx_str, key = parts
            idx = int(idx_str)
            tables.setdefault(tbl, {}).setdefault(idx, {})[key] = value

      # Handle regular Anvil components
    if hasattr(c, "tag") and hasattr(c, "text"):
      # Convert tag to string - it might be None or a ComponentTag object
      tag_str = str(c.tag) if c.tag is not None else ""

      if tag_str.startswith("field_"):
        scalars[tag_str[6:]] = c.text
      elif tag_str.startswith("table_"):
        parts = tag_str.split("_", 3)
        if len(parts) >= 4:
          _, tbl, idx_str, key = parts
          idx = int(idx_str)
          tables.setdefault(tbl, {}).setdefault(idx, {})[key] = c.text

      # Recurse through child components
    if hasattr(c, "get_components"):
      for child in c.get_components():
        walk(child)

  walk(container)

  # Collapse table rows into ordered lists
  for t_name, rows in tables.items():
    scalars[t_name] = [rows[i] for i in sorted(rows)]

  return scalars


def unflatten(flat):
  """Unflatten a dictionary back to nested structure"""
  nested = {}
  for k, v in flat.items():
    parts = k.split(".")
    cur = nested
    for p in parts[:-1]:
      cur = cur.setdefault(p, {})
    cur[parts[-1]] = v
  return nested


def get_final_json(container):
  """Get the final JSON from the edited form"""
  return unflatten(extract_edited_data(container))


# JavaScript helper to extract data from HTML inputs
def get_table_data_js():
  """JavaScript to extract data from HTML table inputs"""
  return """
  function getTableData() {
    const data = {};
    
    // Get all inputs and textareas with data-tag
    document.querySelectorAll('input[data-tag], textarea[data-tag]').forEach(el => {
      const tag = el.getAttribute('data-tag');
      const value = el.value;
      
      if (tag.startsWith('table_')) {
        const parts = tag.split('_');
        const tableName = parts[1];
        const rowIndex = parseInt(parts[2]);
        const colName = parts.slice(3).join('_');
        
        if (!data[tableName]) data[tableName] = [];
        if (!data[tableName][rowIndex]) data[tableName][rowIndex] = {};
        data[tableName][rowIndex][colName] = value;
      }
    });
    
    return data;
  }
  """