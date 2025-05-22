# json_renderer.py

from anvil import *
from anvil import DataGrid, RepeatingPanel, FlowPanel, Label, Spacer, TextBox, TextArea
from ..JsonTableRowForm import JsonTableRowForm  # or wherever your row form is

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

  # 1. Scalars (str, int, float, bool, None) - with labels
  if isinstance(value, (str, int, float, bool)) or value is None:
    if label:
      container.add_component(Label(
        text=f"{label.replace('_', ' ').replace('.', ' > ').title()}:",
        bold=True
      ))

    vstr = "" if value is None else str(value)
    if isinstance(value, str) and (len(value) > 80 or '\n' in value):
      container.add_component(TextArea(text=vstr, width="100%"))
    else:
      container.add_component(TextBox(text=vstr, width="100%"))
    container.add_component(Spacer(height=5))
    return

    # 2. Dicts - group ALL fields by type at the top level
  if isinstance(value, dict):
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
      for k, v in value.items():
        render_json(v, container, label=k, _level=_level+1)
    return

    # 3. Lists
  if isinstance(value, list):
    # Check: List of dicts
    if value and all(isinstance(row, dict) for row in value):
      # Table column headers from union of all dict keys
      keys = sorted({k for row in value for k in row})
      columns = [
        {'id': k, 'title': k.replace('_', ' ').replace('.', ' ').title(), 'data_key': k, 'width': "150px"}
        for k in keys
      ]
      datagrid = DataGrid(columns=columns, rows_per_page=10)
      rp = RepeatingPanel(item_template=JsonTableRowForm)
      rp.items = value

      # Item template as a Form (best) or function
      def item_template(row=None, **properties):
        flow = FlowPanel()
        for k in keys:
          val = row.get(k, "")
          if isinstance(val, str) and (len(val) > 80 or '\n' in val):
            comp = TextArea(text=str(val), width="100%")
          else:
            comp = TextBox(text=str(val), width="100%")
          flow.add_component(comp, width="150px")
        return flow

      rp.item_template = item_template
      datagrid.add_component(rp)
      table_name = label.replace('_', ' ').replace('.', ' > ').title() if label else "Table"
      container.add_component(Label(text=f"{table_name}: {len(value)} rows", bold=True))
      container.add_component(Spacer(height=5))
      container.add_component(datagrid)
      container.add_component(Spacer(height=10))
      return

      # Otherwise, treat as list of scalars or nested lists
    else:
      for idx, item in enumerate(value):
        render_json(item, container, label=f"{label}[{idx}]", _level=_level+1)
      return

  # Fallback for anything else
  container.add_component(Label(text=f"(Unrenderable: {repr(value)})"))
