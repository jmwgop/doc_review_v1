# json_renderer.py – layout-aware rendering

"""Client-side utilities to render extracted JSON into editable Anvil
components, honoring the layout/group definitions stored in the *schema* and
*config* tables.  Falls back to a legacy renderer if no schema bundle is
supplied so old documents still display.
"""

from anvil import *
from ..HtmlTablePanel import HtmlTablePanel
from collections import defaultdict

# ──────────────────────────────────────────────────────────────────────────────
# Helper functions
# ──────────────────────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────────────────────
# Smart pop-up editor for long text fields
# ─────────────────────────────────────────────────────────────────────────────
def _install_popout_editor(widget):
  """When *widget* (TextArea/TextBox) gains focus, open a big
    floating editor IF the content is long enough to warrant it.
    Only shows popout for content > 100 chars OR content with line breaks."""

  def _open_editor(**evt):
    current_text = widget.text or ""

    # Only show popout if content is long or has line breaks
    if len(current_text) <= 100 and '\n' not in current_text:
      return  # Let the field behave normally for short content

    # build a large TextArea pre-filled with the current text
    big = TextArea(text=current_text, width="100%", height="400px")

    # show it in an Anvil alert dialog
    ok = alert(big,
               large=True,
               title="Edit Long Text",
               buttons=[("Save", True), ("Cancel", False)])

    # if user clicked Save, commit changes
    if ok:
      widget.text = big.text

  # bind to focus event
  widget.set_event_handler("focus", _open_editor)


def dig(data, path_parts):
  """Safely traverse *data* (a dict) by successive keys in *path_parts*.

    Returns *None* if any intermediate is missing or not a dict.
    """
  cur = data
  for part in path_parts:
    if isinstance(cur, dict):
      cur = cur.get(part)
    else:
      return None
  return cur


def prettify(path):
  """Human-friendly label from a JSON path (use last segment)."""
  return path.split(".")[-1].replace("_", " ").title()

# ──────────────────────────────────────────────────────────────────────────────
#  Public entry
# ──────────────────────────────────────────────────────────────────────────────

def render_json(payload, container, *, schema_bundle=None):
  """Render *payload* into *container*.

    If *schema_bundle* (from ConfigService.get_full_schema_bundle) is provided
    scalars are grouped and laid out per schema; otherwise we dump everything.
    """
  if schema_bundle:
    _render_with_schema(payload, container, schema_bundle)
  else:
    _legacy_render(payload, container)

# ──────────────────────────────────────────────────────────────────────────────
#  Schema-aware renderer
# ──────────────────────────────────────────────────────────────────────────────

def _render_with_schema(payload, container, bundle):
  layout_spec = bundle.get("structure", {}).get("layout", [])
  field_cfgs  = bundle.get("fields", [])

  # 1️⃣ Index configs & gather scalar values
  cfg_by_path = {c["path"]: c for c in field_cfgs if not c.get("excluded")}
  scalar_values = {p: dig(payload, p.split(".")) for p in cfg_by_path}

  # 2️⃣ Group fields by layout_group
  grouped = defaultdict(list)
  for path, val in scalar_values.items():
    grouped[cfg_by_path[path].get("layout_group") or "_misc"].append(
      (path, val, cfg_by_path[path])
    )
  for g in grouped:
    grouped[g].sort(key=lambda t: t[0])

    # 3️⃣ Render sections top-to-bottom
  rendered = set()
  for section in layout_spec:
    title = section["title"]
    style = section.get("style", "two-column")
    fields = grouped.get(title, [])
    if not fields:
      continue

      # Section header
    container.add_component(Label(text=title, bold=True, font_size=18))
    container.add_component(Spacer(height=4))

    # Layout container
    panel = ColumnPanel() if style == "full-width" else FlowPanel()
    # Layout container
    if style == "two-column":
      panel = FlowPanel()
      panel.role = "json-two-col"

      # build bricks once
      for path, val, cfg in fields:
        rendered.add(path)

        brick = ColumnPanel(width="260px")
        brick.role = "json-two-col-brick"
        panel.add_component(brick)

        label_txt = cfg.get("label_override") or prettify(path)
        brick.add_component(Label(text=f"{label_txt}:", bold=True))

        widget_cls = TextArea if cfg["widget_type"] == "TextArea" else TextBox
        w = widget_cls(text="" if val is None else str(val), width="100%")
        w.tag = f"field_{path}"
        w.role = "expand-on-focus"
        _install_popout_editor(w)             # ← add this
        brick.add_component(w)

      container.add_component(panel)      # ← add the panel once
      container.add_component(Spacer(height=12))
      continue     # 🚀 skip the generic loop below for this section
    else:
      panel = ColumnPanel()
      container.add_component(panel)      # ← add the panel!
    # Fields
    for path, val, cfg in fields:
      rendered.add(path)
      label_txt = cfg.get("label_override") or prettify(path)
      panel.add_component(Label(text=f"{label_txt}:", bold=True))

      widget_cls = TextArea if cfg["widget_type"] == "TextArea" else TextBox
      w = widget_cls(text="" if val is None else str(val), width="100%")
      w.tag = f"field_{path}"
      w.role = "expand-on-focus"
      _install_popout_editor(w)             # ← add this
      panel.add_component(w)
      panel.add_component(Spacer(height=4, width=12))

    container.add_component(Spacer(height=12))

    # 4️⃣ Misc group for unrendered scalars
  misc_paths = [p for p in cfg_by_path if p not in rendered]
  if misc_paths:
    container.add_component(Label(text="Misc", bold=True, font_size=18))
    misc_panel = ColumnPanel()
    container.add_component(misc_panel)
    for path in misc_paths:
      cfg = cfg_by_path[path]
      label_txt = cfg.get("label_override") or prettify(path)
      misc_panel.add_component(Label(text=f"{label_txt}:", bold=True))
      widget_cls = TextArea if cfg["widget_type"] == "TextArea" else TextBox
      v = scalar_values[path]
      w = widget_cls(text="" if v is None else str(v), width="100%")
      w.tag = f"field_{path}"
      w.role = "expand-on-focus"
      _install_popout_editor(w)             # ← add this
      misc_panel.add_component(w)
      misc_panel.add_component(Spacer(height=4))
    container.add_component(Spacer(height=12))

    # 5️⃣ Render all tables/lists
  _render_tables(payload, container)

# ──────────────────────────────────────────────────────────────────────────────
#  Legacy renderer (kept so old docs still work)
# ──────────────────────────────────────────────────────────────────────────────

def _legacy_render(value, container, label=None, _level=0):
  """Former recursive renderer – used when no schema info is available."""
  if isinstance(value, (str, int, float, bool)) or value is None:
    if label:
      container.add_component(Label(text=f"{label.replace('_',' ').replace('.',' > ').title()}:", bold=True))
    vstr = "" if value is None else str(value)
    widget_cls = TextArea if isinstance(value, str) and (len(vstr) > 80 or "\n" in vstr) else TextBox
    w = widget_cls(text=vstr, width="100%")
    w.tag = f"field_{label}"
    w.role = "expand-on-focus"
    _install_popout_editor(w)             # ← add this
    container.add_component(w)
    container.add_component(Spacer(height=5))
    return

  if isinstance(value, dict):
    scalars, tables = collect_fields_by_type(value)
    for p, v in scalars:
      _legacy_render(v, container, label=p, _level=_level+1)
    if tables:
      container.add_component(Spacer(height=20))
      for p, v in tables:
        _legacy_render(v, container, label=p, _level=_level+1)
    return

  if isinstance(value, list):
    if value and isinstance(value[0], dict):
      _render_table(label, value, container)
    else:
      for item in value:
        _legacy_render(item, container, _level=_level+1)
    return

  container.add_component(Label(text=f"(Unrenderable: {repr(value)})"))

# ──────────────────────────────────────────────────────────────────────────────
#  Table helpers (HTML-table rendering)
# ──────────────────────────────────────────────────────────────────────────────

def _render_tables(payload, container):
  _, tables = collect_fields_by_type(payload)
  if not tables:
    return
  container.add_component(Spacer(height=20))
  for path, rows in tables:
    _render_table(path, rows, container)


def _render_table(label, rows, container):
  """Render a list-of-dict rows as an HTML table inside *container*."""
  flat = [flatten_dict(r) for r in rows]
  keys = sorted({k for r in flat for k in r})
  if not keys:
    return

    # ─── column widths ────────────────────────────────────────────────────
  col_w = {}
  for k in keys:
    w = max(len(k)*10, 120)
    for r in flat:
      t = str(r.get(k, ""))
      w = max(w, 280 if len(t) > 80 or "\n" in t else min(len(t)*8+20, 200))
    col_w[k] = w
  total = sum(col_w.values()) + 50
  min_w = "100%" if len(keys) <= 3 else f"{total}px"
  layout = "auto" if len(keys) <= 3 else "fixed"

  # ─── stylesheet & skeleton ────────────────────────────────────────────
  html = [
    "<style>",
    ".json-table-container{width:100%;overflow-x:auto;overflow-y:auto;"
    "border:1px solid #ddd;border-radius:4px;background:#faf9fa;"
    "margin-bottom:10px;max-height:400px;}",
    f".json-table{{width:100%;min-width:{min_w};border-collapse:collapse;table-layout:{layout};}}",
    ".json-table th{background:#f5f5f5;font-weight:bold;position:sticky;top:0;padding:8px;border:1px solid #ddd;text-align:center;}",
    ".json-table td{padding:8px;border:1px solid #ddd;text-align:center;}",
  ]
  for idx, k in enumerate(keys):
    html.append(
      f".json-table th:nth-child({idx+1}),.json-table td:nth-child({idx+1}){{{{width:{col_w[k]}px;min-width:{col_w[k]}px;}}}}"
    )
  html += [
    ".json-table tr:nth-child(even){background:#f9f9f9;}",
    ".json-table input[type='text'],.json-table textarea{width:calc(100% - 8px);border:1px solid #e0e0e0;background:white;font-family:inherit;font-size:inherit;padding:4px;margin:0;text-align:left;}",
    ".json-table textarea{height:60px;resize:vertical;}",
    # ADD: Click handler for popout editor on table fields
    ".json-table input[type='text']:focus,.json-table textarea:focus{outline:2px solid #4285f4;outline-offset:1px;}",
    "</style>",
    "<div class='json-table-container'><table class='json-table'>",
    "<thead><tr>",
  ]

  # header row
  for k in keys:
    html.append(f"<th>{k.replace('_',' ').title()}</th>")
  html.append("</tr></thead><tbody>")

  # data rows
  for i, row in enumerate(flat):
    html.append("<tr>")
    for k in keys:
      cell = str(row.get(k, ""))
      esc = (cell.replace("&", "&amp;").replace("<", "&lt;")
        .replace(">", "&gt;").replace("\"", "&quot;"))

      # ADD: onclick handler for popout editor
      if len(cell) > 80 or "\n" in cell:
        inp = f"<textarea data-tag='table_{label}_{i}_{k}' onclick='openTablePopout(this)'>{esc}</textarea>"
      else:
        inp = f"<input type='text' value='{esc}' data-tag='table_{label}_{i}_{k}' onclick='openTablePopout(this)'/>"
      html.append(f"<td>{inp}</td>")
    html.append("</tr>")
  html.append("</tbody></table></div>")

  # insert into Anvil
  tbl_panel = HtmlTablePanel()
  tbl_panel.html = "".join(html)

  title = label.replace('_',' ').replace('.', ' > ').title() if label else "Table"
  container.add_component(Label(text=f"{title}: {len(rows)} rows", bold=True))
  container.add_component(Spacer(height=5))
  container.add_component(tbl_panel)
  container.add_component(Spacer(height=10))

# ──────────────────────────────────────────────────────────────────────────────
#  Shared helper utilities (unchanged from original version)
# ──────────────────────────────────────────────────────────────────────────────

def flatten_dict(d, parent_key='', sep='_'):
  items = []
  for k, v in d.items():
    new_key = f"{parent_key}{sep}{k}" if parent_key else k
    if isinstance(v, dict):
      items.extend(flatten_dict(v, new_key, sep=sep).items())
    else:
      items.append((new_key, v))
  return dict(items)


def collect_fields_by_type(value, parent_key='', scalar_fields=None, table_fields=None):
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


def extract_edited_data(container):
  """Walk the rendered form and pull out edited scalar & table values."""
  scalars, tables = {}, {}

  def walk(c):
    if hasattr(c, 'get_table_data'):
      for tag_str, val in c.get_table_data().items():
        if tag_str.startswith('table_'):
          _tag_table_to_dict(tag_str, val, tables)

    if hasattr(c, 'tag') and hasattr(c, 'text'):
      tag = str(c.tag) if c.tag is not None else ""
      if tag.startswith('field_'):
        scalars[tag[6:]] = c.text
      elif tag.startswith('table_'):
        _tag_table_to_dict(tag, c.text, tables)

    if hasattr(c, 'get_components'):
      for child in c.get_components():
        walk(child)

  def _tag_table_to_dict(tag_str, value, dest):
    _, tbl, idx_str, key = tag_str.split('_', 3)
    idx = int(idx_str)
    dest.setdefault(tbl, {}).setdefault(idx, {})[key] = value

  walk(container)

  for t_name, rows in tables.items():
    scalars[t_name] = [rows[i] for i in sorted(rows)]

  return scalars


def unflatten(flat):
  nested = {}
  for k, v in flat.items():
    cur = nested
    parts = k.split('.')
    for p in parts[:-1]:
      cur = cur.setdefault(p, {})
    cur[parts[-1]] = v
  return nested


def get_final_json(container):
  return unflatten(extract_edited_data(container))

# JS helper for HtmlTablePanel

def get_table_data_js():
  return """
    function getTableData() {
      const data = {};
      document.querySelectorAll('input[data-tag], textarea[data-tag]').forEach(el => {
        const tag = el.getAttribute('data-tag');
        const value = el.value;
        if (tag.startsWith('table_')) {
          const parts = tag.split('_');
          const tbl  = parts[1];
          const idx  = parseInt(parts[2]);
          const key  = parts.slice(3).join('_');
          if (!data[tbl]) data[tbl] = [];
          if (!data[tbl][idx]) data[tbl][idx] = {};
          data[tbl][idx][key] = value;
        }
      });
      return data;
    }
    
    // NEW: Popout editor for table fields
    function openTablePopout(element) {
      const currentText = element.value;
      
      // Only show popout if content is long or has line breaks
      if (currentText.length <= 100 && !currentText.includes('\\n')) {
        return; // Let the field behave normally for short content
      }
      
      // Create a modal overlay
      const overlay = document.createElement('div');
      overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.5);
        z-index: 9999;
        display: flex;
        align-items: center;
        justify-content: center;
      `;
      
      // Create the modal content
      const modal = document.createElement('div');
      modal.style.cssText = `
        background: white;
        padding: 20px;
        border-radius: 8px;
        width: 80%;
        max-width: 800px;
        max-height: 80%;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
      `;
      
      // Create the textarea
      const textarea = document.createElement('textarea');
      textarea.value = currentText;
      textarea.style.cssText = `
        width: 100%;
        height: 400px;
        margin-bottom: 15px;
        padding: 10px;
        border: 1px solid #ddd;
        border-radius: 4px;
        font-family: inherit;
        font-size: 14px;
        resize: vertical;
      `;
      
      // Create buttons
      const buttonContainer = document.createElement('div');
      buttonContainer.style.cssText = 'text-align: right;';
      
      const saveBtn = document.createElement('button');
      saveBtn.textContent = 'Save';
      saveBtn.style.cssText = `
        background: #4285f4;
        color: white;
        border: none;
        padding: 8px 16px;
        margin-left: 10px;
        border-radius: 4px;
        cursor: pointer;
      `;
      
      const cancelBtn = document.createElement('button');
      cancelBtn.textContent = 'Cancel';
      cancelBtn.style.cssText = `
        background: #f8f9fa;
        color: #333;
        border: 1px solid #ddd;
        padding: 8px 16px;
        border-radius: 4px;
        cursor: pointer;
      `;
      
      // Add event listeners
      saveBtn.onclick = () => {
        element.value = textarea.value;
        document.body.removeChild(overlay);
      };
      
      cancelBtn.onclick = () => {
        document.body.removeChild(overlay);
      };
      
      // Close on overlay click
      overlay.onclick = (e) => {
        if (e.target === overlay) {
          document.body.removeChild(overlay);
        }
      };
      
      // Close on Escape key
      document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
          document.body.removeChild(overlay);
        }
      }, { once: true });
      
      // Assemble the modal
      buttonContainer.appendChild(cancelBtn);
      buttonContainer.appendChild(saveBtn);
      modal.appendChild(textarea);
      modal.appendChild(buttonContainer);
      overlay.appendChild(modal);
      
      // Show the modal
      document.body.appendChild(overlay);
      
      // Focus the textarea
      setTimeout(() => textarea.focus(), 100);
    }
    """