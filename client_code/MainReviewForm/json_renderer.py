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

def create_real_editable_table(data_list, container, label=None):
  """
  Creates a table using real Anvil components that look like HTML tables
  but are actually accessible to Python code.
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

  # Create M3 Card using ColumnPanel with outlined-card role for horizontal scrolling
  scroll_wrapper = ColumnPanel(
    role="outlined-card"
  )

  table_container = ColumnPanel(
    background="#ffffff"
  )

  # Create header row using FlowPanel with tight spacing
  header_panel = FlowPanel(spacing="tight")
  header_panel.background = "#f5f5f5"

  for key in all_keys:
    header_label = Label(
      text=key.replace('_', ' ').title(),
      bold=True,
      width="180px",  # Consistent fixed width
      align="center",
      background="#f5f5f5",
      foreground="#333"
    )
    header_label.border = "1px solid #ddd"
    header_label.spacing = "tight"
    header_panel.add_component(header_label)

  table_container.add_component(header_panel)

  # Create data rows with real editable components
  for i, row_data in enumerate(flat_rows):
    bg_color = "#fafafa" if i % 2 == 1 else "#ffffff"

    row_panel = FlowPanel()
    row_panel.background = bg_color
    row_panel.spacing = "none"

    for key in all_keys:
      cell_value = row_data.get(key, "")
      str_value = "" if cell_value is None else str(cell_value)

      # Create real editable Anvil component
      if len(str_value) > 80 or '\n' in str_value:
        cell_component = TextArea(
          text=str_value,
          height="60px"
        )
      else:
        cell_component = TextBox(text=str_value)

      # Style to look like table cell
      cell_component.width = "200px"  # Match header width
      cell_component.background = "#ffffff"
      cell_component.border = "1px solid #ddd"
      cell_component.align = "center"

      # Store reference for data extraction later
      cell_component.tag = f"table_{label}_{i}_{key}"

      row_panel.add_component(cell_component)

    table_container.add_component(row_panel)

  scroll_wrapper.add_component(table_container)
  container.add_component(scroll_wrapper)
  container.add_component(Spacer(height=20))

def render_json(value, container, label=None, _level=0):
  """
  Renders JSON with real editable Anvil components.
  """
  if label is not None:
    print(f"[RENDER] Section label: {label}")

  # 1. Scalars - real TextBox/TextArea components
  if isinstance(value, (str, int, float, bool)) or value is None:
    if label:
      container.add_component(Label(
        text=f"{label.replace('_', ' ').replace('.', ' > ').title()}:",
        bold=True
      ))

    vstr = "" if value is None else str(value)
    if isinstance(value, str) and (len(value) > 80 or '\n' in value):
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

  # 3. Lists - use real components that look like tables
  if isinstance(value, list):
    if value and isinstance(value[0], dict):
      create_real_editable_table(value, container, label)
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
          if table_name not in edited_data:
            edited_data[table_name] = {}
          if row_idx not in edited_data[table_name]:
            edited_data[table_name][row_idx] = {}
          edited_data[table_name][row_idx][key] = comp.text

    # Recursively check child components
    if hasattr(comp, 'get_components'):
      for child in comp.get_components():
        traverse_components(child)

  traverse_components(container)
  return edited_data