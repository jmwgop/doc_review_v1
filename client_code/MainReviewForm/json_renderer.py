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

def is_likely_long_field(field_name, value):
  """Return True if value is a long string; ignore field_name completely."""
  return isinstance(value, str) and (len(value) > 40 or '\n' in value)

def assign_column_roles(keys, example_row):
  """Assign column roles purely based on content length."""
  roles = []
  for key in keys:
    value = example_row.get(key, "")
    if is_likely_long_field(None, value):
      roles.append("anvil-role-json-table-cell anvil-role-json-col-wide json-col-wide")
    else:
      roles.append("anvil-role-json-table-cell anvil-role-json-col-narrow json-col-narrow")
  return roles

def create_table_with_anvil_components(data_list, container, label=None):
  """
    Creates a responsive, scrollable table using Anvil components and roles for proper CSS styling.
    Column widths are set via roles for flexible sizing and scroll support, based ONLY on content length.
    """
  if not data_list:
    container.add_component(Label(text="(No data)"))
    return

    # Table label
  table_name = label.replace('_', ' ').replace('.', ' > ').title() if label else "Table"
  container.add_component(Label(text=f"{table_name}: {len(data_list)} rows", bold=True))
  container.add_component(Spacer(height=5))

  # Flatten each row
  flat_rows = [flatten_dict(row) for row in data_list]
  all_keys = list(dict.fromkeys(k for row in flat_rows for k in row))  # preserve order

  if not all_keys:
    container.add_component(Label(text="(No fields found)"))
    return

    # Assign column roles: wide or narrow (content-based only)
  roles = assign_column_roles(all_keys, flat_rows[0] if flat_rows else {})

  # Outer scrollable container
  outer_container = ColumnPanel()
  outer_container.role = "json-table-container"

  # Inner wrapper (stretches to content width)
  inner_panel = LinearPanel()
  inner_panel.role = "json-table-wrapper json-table-dynamic"
  inner_panel.width = "auto"  # Let CSS/roles control width

  # === HEADER ROW ===
  header_row = FlowPanel(spacing="none")
  header_row.role = "json-table-row json-header-row json-no-spacing"
  for key, role in zip(all_keys, roles):
    header_cell = Label(
      text=key.replace('_', ' ').replace('.', ' > ').title(),
      bold=True,
      role=role
    )
    header_row.add_component(header_cell)
  inner_panel.add_component(header_row)

  # === DATA ROWS ===
  for row_idx, row_data in enumerate(flat_rows):
    row_role = "json-row-even" if row_idx % 2 == 0 else "json-row-odd"
    data_row = FlowPanel(spacing="none")
    data_row.role = f"json-table-row {row_role} json-no-spacing"

    for col_idx, (key, role) in enumerate(zip(all_keys, roles)):
      cell_value = row_data.get(key, "")
      str_value = "" if cell_value is None else str(cell_value)
      # Choose input type
      if len(str_value) > 80 or '\n' in str_value:
        cell_component = TextArea(
          text=str_value,
          placeholder="",
          role=f"{role} json-data-cell"
        )
      else:
        cell_component = TextBox(
          text=str_value,
          placeholder="",
          role=f"{role} json-data-cell"
        )
        # Set tag and add to row (for both input types)
      cell_component.tag = f"table_{label}_{row_idx}_{key}"
      data_row.add_component(cell_component)

      # After all cells for this row:
    inner_panel.add_component(data_row)

    # Add to outer container once, after all rows are built
  outer_container.add_component(inner_panel)
  container.add_component(outer_container)
  container.add_component(Spacer(height=12))

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
        scalar_fields.append((new_key, v))
      elif isinstance(v, list) and v and isinstance(v[0], dict):
        table_fields.append((new_key, v))
      elif isinstance(v, dict):
        collect_fields_by_type(v, new_key, scalar_fields, table_fields)

  return scalar_fields, table_fields

def render_json(value, container, label=None, _level=0):
  """
    Recursively renders JSON into Anvil container as editable inputs, styled by role.
    """
  # Scalars
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
    field_component.tag = f"field_{label}"
    container.add_component(field_component)
    container.add_component(Spacer(height=5))
    return

    # Dicts: top-level, group fields and tables
  if isinstance(value, dict):
    if _level == 0:
      # Group scalar and table fields
      scalar_fields, table_fields = collect_fields_by_type(value)
      for field_path, field_value in scalar_fields:
        render_json(field_value, container, label=field_path, _level=_level+1)
      if table_fields:
        container.add_component(Spacer(height=20))
        for table_path, table_value in table_fields:
          render_json(table_value, container, label=table_path, _level=_level+1)
    else:
      for k, v in value.items():
        render_json(v, container, label=k, _level=_level+1)
    return

    # Lists
  if isinstance(value, list):
    if value and isinstance(value[0], dict):
      create_table_with_anvil_components(value, container, label)
      return
    else:
      for idx, item in enumerate(value):
        render_json(item, container, _level=_level+1)
      return

    # Fallback
  container.add_component(Label(text=f"(Unrenderable: {repr(value)})"))

def extract_edited_data(container):
  """
    Extract current values from editable components. Uses .tag to rebuild data structure.
    """
  edited_data = {}
  table_data = {}

  def traverse_components(comp):
    if hasattr(comp, 'tag') and comp.tag:
      if hasattr(comp, 'text'):
        if comp.tag.startswith('field_'):
          field_name = comp.tag[6:]
          edited_data[field_name] = comp.text
        elif comp.tag.startswith('table_'):
          parts = comp.tag.split('_', 3)
          if len(parts) >= 4:
            table_name, row_idx, key = parts[1], int(parts[2]), parts[3]
            if table_name not in table_data:
              table_data[table_name] = {}
            if row_idx not in table_data[table_name]:
              table_data[table_name][row_idx] = {}
            table_data[table_name][row_idx][key] = comp.text
    if hasattr(comp, 'get_components'):
      for child in comp.get_components():
        traverse_components(child)

  traverse_components(container)

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
