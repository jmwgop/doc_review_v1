from anvil import *

# ---------- small helpers ----------

def flatten_dict(d, parent_key="", sep="_"):
  items = []
  for k, v in d.items():
    new_key = f"{parent_key}{sep}{k}" if parent_key else k
    if isinstance(v, dict):
      items.extend(flatten_dict(v, new_key, sep=sep).items())
    else:
      items.append((new_key, v))
  return dict(items)


def is_long_string(s):
  return isinstance(s, str) and (len(s) > 40 or "\n" in s)


# ---------- table building ----------

def assign_column_roles(keys, example_row):
  roles = []
  for k in keys:
    if is_long_string(example_row.get(k, "")):
      roles.append("json-table-cell json-col-wide")
    else:
      roles.append("json-table-cell json-col-narrow")
  return roles


def create_table_with_anvil_components(data, container, label=None):
  if not data:
    container.add_component(Label(text="(No data)"))
    return

  table_name = (label or "Table").replace("_", " ").replace(".", " > ").title()
  container.add_component(Label(text=f"{table_name}: {len(data)} rows", bold=True))
  container.add_component(Spacer(height=5))

  flat_rows = [flatten_dict(r) for r in data]
  all_keys = list(dict.fromkeys(k for row in flat_rows for k in row))
  roles = assign_column_roles(all_keys, flat_rows[0])

  outer = ColumnPanel(role="json-table-container")

  wrapper = LinearPanel(role="json-table-wrapper json-table-dynamic")
  wrapper.width = "auto"

  # ----- header -----
  header = FlowPanel(spacing="none", role="json-table-row json-header-row json-no-spacing")
  for k, role in zip(all_keys, roles):
    # Determine width based on role
    width = "260px" if "json-col-wide" in role else "160px"
    header.add_component(
      Label(text=k.replace("_", " ").replace(".", " > ").title(),
            bold=True, role=role),
      width=width  # ADD THIS
    )
  wrapper.add_component(header)

  # ----- body -----
  for r_i, row in enumerate(flat_rows):
    body_row = FlowPanel(
      spacing="none",
      role=f"json-table-row {'json-row-even' if r_i % 2 == 0 else 'json-row-odd'} json-no-spacing",
    )
    for k, role in zip(all_keys, roles):
      val = row.get(k, "")
      txt = "" if val is None else str(val)
      width = "260px" if "json-col-wide" in role else "160px"  # ADD THIS
      if is_long_string(txt):
        comp = TextArea(text=txt, role=f"{role} json-data-cell")
      else:
        comp = TextBox(text=txt, role=f"{role} json-data-cell")
      comp.tag = f"table_{label}_{r_i}_{k}"
      body_row.add_component(comp, width=width)  # ADD WIDTH HERE
    wrapper.add_component(body_row)

  outer.add_component(wrapper)
  container.add_component(outer)
  container.add_component(Spacer(height=12))


# ---------- JSON renderer ----------

def collect_fields_by_type(value, parent_key="", scalars=None, tables=None):
  scalars = scalars or []
  tables = tables or []
  if isinstance(value, dict):
    for k, v in value.items():
      new_key = f"{parent_key}.{k}" if parent_key else k
      if isinstance(v, (str, int, float, bool)) or v is None:
        scalars.append((new_key, v))
      elif isinstance(v, list) and v and isinstance(v[0], dict):
        tables.append((new_key, v))
      elif isinstance(v, dict):
        collect_fields_by_type(v, new_key, scalars, tables)
  return scalars, tables


def render_json(value, container, label=None, _lvl=0):
  # --- simple scalar ---
  if isinstance(value, (str, int, float, bool)) or value is None:
    if label:
      container.add_component(Label(text=f"{label.replace('_', ' ').replace('.', ' > ').title()}:", bold=True))
    txt = "" if value is None else str(value)
    widget = TextArea if is_long_string(txt) else TextBox
    field = widget(text=txt, width="100%")
    field.tag = f"field_{label}"
    container.add_component(field)
    container.add_component(Spacer(height=5))
    return

    # --- dict ---
  if isinstance(value, dict):
    if _lvl == 0:
      scalars, tables = collect_fields_by_type(value)
      for p, v in scalars:
        render_json(v, container, label=p, _lvl=_lvl + 1)
      if tables:
        container.add_component(Spacer(height=20))
        for p, v in tables:
          render_json(v, container, label=p, _lvl=_lvl + 1)
    else:
      for k, v in value.items():
        render_json(v, container, label=k, _lvl=_lvl + 1)
    return

    # --- list ---
  if isinstance(value, list):
    if value and isinstance(value[0], dict):
      create_table_with_anvil_components(value, container, label)
    else:
      for item in value:
        render_json(item, container, _lvl=_lvl + 1)
    return

    # --- fallback ---
  container.add_component(Label(text=f"(Unrenderable: {repr(value)})"))


# ---------- extraction helpers ----------

def extract_edited_data(container):
  scalars, tables = {}, {}

  def walk(c):
    if getattr(c, "tag", None) and hasattr(c, "text"):
      if c.tag.startswith("field_"):
        scalars[c.tag[6:]] = c.text
      elif c.tag.startswith("table_"):
        _, tbl, idx, key = c.tag.split("_", 3)
        idx = int(idx)
        tables.setdefault(tbl, {}).setdefault(idx, {})[key] = c.text
    if hasattr(c, "get_components"):
      for child in c.get_components():
        walk(child)

  walk(container)

  # collapse table rows into ordered lists
  for t_name, rows in tables.items():
    scalars[t_name] = [rows[i] for i in sorted(rows)]

  return scalars


def unflatten(flat):
  nested = {}
  for k, v in flat.items():
    parts = k.split(".")
    cur = nested
    for p in parts[:-1]:
      cur = cur.setdefault(p, {})
    cur[parts[-1]] = v
  return nested


def get_final_json(container):
  return unflatten(extract_edited_data(container))
