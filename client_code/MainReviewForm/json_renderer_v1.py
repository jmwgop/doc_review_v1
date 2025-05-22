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

def collect_fields_by_type(value, parent_key='', scalar_fields=None, table_fields=None):
  """
  Recursively collects all scalar fields and table fields from the entire JSON structure.
  """
  if scalar_fields is None:
    scalar_fields = []
  if table_fields is None:
    table_fields = []

  if isinstance(value, dict):
    for k, v in value.items():
      new_key = f"{parent_key}.{k}" if parent_key else k

      if isinstance(v, (str, int, float, bool)) or v is None:
        scalar_fields.append((new_key, v))
      elif isinstance(v, list) and v and isinstance(v[0], dict):
        table_fields.append((new_key, v))
      elif isinstance(v, dict):
        collect_fields_by_type(v, new_key, scalar_fields, table_fields)

  return scalar_fields, table_fields

def create_hybrid_table(data_list, container, label=None):
  """
  Creates a compact, scrollable table that looks like HTML but uses real Anvil components.
  """
  if not data_list:
    container.add_component(Label(text="(No data)"))
    return

  # Add table name
  table_name = label.replace('_', ' ').replace('.', ' > ').title() if label else "Table"
  container.add_component(Label(text=f"{table_name}: {len(data_list)} rows", bold=True))
  container.add_component(Spacer(height=5))

  # Flatten all rows and get unique keys
  flat_rows = [flatten_dict(row) for row in data_list]
  all_keys = sorted({k for row in flat_rows for k in row})

  if not all_keys:
    container.add_component(Label(text="(No fields found)"))
    return

  num_cols = len(all_keys)

  # Better column sizing - give more space per column
  if num_cols <= 4:
    col_width = 3  # Wider columns for few columns
  elif num_cols <= 8:
    col_width = 2  # Medium columns 
  else:
    col_width = 1  # Still decent width for many columns

  # Create outer container with horizontal scroll capability
  outer_container = ColumnPanel()
  outer_container.border = "1px solid #ddd"
  outer_container.role = "outlined-card"

  # Add scroll hint for wide tables
  if num_cols > 6:
    scroll_hint = Label(
      text="← Scroll horizontally for more columns →", 
      italic=True, 
      align="center",
      foreground="#666"
    )
    outer_container.add_component(scroll_hint)
    outer_container.add_component(Spacer(height=3))

  # Create scrollable content - LEFT ALIGNED
  content_panel = ColumnPanel()
  if num_cols > 6:
    # Force horizontal scroll with wider minimum
    content_panel.width = f"{num_cols * 150}px"  # 150px per column

  # Create compact GridPanel with LEFT alignment
  grid = GridPanel()

  # === CREATE HEADER ROW ===
  for col_idx, key in enumerate(all_keys):
    header_label = Label(
      text=key.replace('_', ' ').title(),
      bold=True,
      align="left",  # Left align headers
      background="#f5f5f5",
      foreground="#333"
    )
    header_label.border = "1px solid #ddd"

    grid.add_component(header_label, row=0, col_pos=col_idx, width_xs=col_width, col_xs=0)

  # === CREATE DATA ROWS - COMPACT ===
  for row_idx, row_data in enumerate(flat_rows):

    for col_idx, key in enumerate(all_keys):
      cell_value = row_data.get(key, "")
      str_value = "" if cell_value is None else str(cell_value)

      # Create compact editable components - NO AUTO EXPAND
      if len(str_value) > 100 or '\n' in str_value:
        cell_component = TextArea(
          text=str_value,
          height="50px"  # FIXED HEIGHT
        )
      else:
        cell_component = TextBox(
          text=str_value,
          placeholder="Enter value..."
        )

      # Minimal styling for compactness
      cell_component.background = "#ffffff"
      cell_component.border = "1px solid #ddd"

      # Store reference for data extraction
      cell_component.tag = f"table_{label}_{row_idx}_{key}"

      # Add to grid - same column width as header, LEFT ALIGNED
      grid.add_component(cell_component, row=row_idx+1, col_pos=col_idx, width_xs=col_width, col_xs=0)

  content_panel.add_component(grid)
  outer_container.add_component(content_panel)
  container.add_component(outer_container)
  container.add_component(Spacer(height=15))

def render_json(value, container, label=None, _level=0):
  """
  Renders JSON with real editable Anvil components that look like HTML tables.
  """
  # 1. Scalars - real TextBox/TextArea components
  if isinstance(value, (str, int, float, bool)) or value is None:
    if label:
      container.add_component(Label(
        text=f"{label.replace('_', ' ').replace('.', ' > ').title()}:",
        bold=True
      ))

    vstr = "" if value is None else str(value)
    if isinstance(value, str) and (len(vstr) > 80 or '\n' in vstr):
      field_component = TextArea(text=vstr, width="100%")
    else:
      field_component = TextBox(text=vstr, width="100%")

    # Store reference for data extraction
    field_component.tag = f"field_{label}"
    container.add_component(field_component)
    container.add_component(Spacer(height=5))
    return

  # 2. Dicts - group by type at top level
  if isinstance(value, dict):
    if _level == 0:
      scalar_fields, table_fields = collect_fields_by_type(value)

      # Render all scalar fields first
      if scalar_fields:
        for field_path, field_value in scalar_fields:
          render_json(field_value, container, label=field_path, _level=_level+1)

      # Then render all tables
      if table_fields:
        container.add_component(Spacer(height=20))
        for table_path, table_value in table_fields:
          render_json(table_value, container, label=table_path, _level=_level+1)
    else:
      for k, v in value.items():
        render_json(v, container, label=k, _level=_level+1)
    return

  # 3. Lists - use hybrid table approach
  if isinstance(value, list):
    if value and isinstance(value[0], dict):
      create_hybrid_table(value, container, label)
      return
    else:
      for idx, item in enumerate(value):
        render_json(item, container, _level=_level+1)
      return

  # Fallback
  container.add_component(Label(text=f"(Unrenderable: {repr(value)})"))

def extract_edited_data(container):
  """
  Extracts current values from all editable components.
  Uses the .tag property to identify components and rebuild data structure.
  """
  edited_data = {}
  table_data = {}

  def traverse_components(comp):
    if hasattr(comp, 'tag') and comp.tag and hasattr(comp, 'text'):
      if comp.tag.startswith('field_'):
        field_name = comp.tag[6:]  # Remove 'field_' prefix
        edited_data[field_name] = comp.text
      elif comp.tag.startswith('table_'):
        # Handle table data extraction
        parts = comp.tag.split('_', 3)  # table_label_row_key
        if len(parts) >= 4:
          table_name, row_idx, key = parts[1], int(parts[2]), parts[3]
          if table_name not in table_data:
            table_data[table_name] = {}
          if row_idx not in table_data[table_name]:
            table_data[table_name][row_idx] = {}
          table_data[table_name][row_idx][key] = comp.text

    # Recursively check child components
    if hasattr(comp, 'get_components'):
      for child in comp.get_components():
        traverse_components(child)

  traverse_components(container)

  # Convert table data to proper list format
  for table_name, rows in table_data.items():
    row_list = []
    for i in sorted(rows.keys()):
      row_list.append(rows[i])
    edited_data[table_name] = row_list

  return edited_data

def unflatten_data(flat_data):
  """
  Converts flattened data back to nested structure.
  Example: {'a.b.c': 'value'} -> {'a': {'b': {'c': 'value'}}}
  """
  result = {}

  for key, value in flat_data.items():
    parts = key.split('.')
    current = result

    for part in parts[:-1]:
      if part not in current:
        current[part] = {}
      current = current[part]

    current[parts[-1]] = value

  return result

def get_final_json(container):
  """
  Extracts all edited data and returns it as properly structured JSON.
  """
  flat_data = extract_edited_data(container)
  return unflatten_data(flat_data)