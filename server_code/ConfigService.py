# ConfigService.py  (server-side)
#
# Exposes read-only helpers for schema/layout information so the client
# renderer can build grouped forms without talking to Data Tables directly.

import anvil.server
import anvil.tables.query as q
from anvil.tables import app_tables
from functools import lru_cache
from datetime import datetime


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _now_iso():
  return datetime.utcnow().isoformat(timespec="seconds") + "Z"

def _schema_row(schema_name):
  """Return the single row from `schema` table with this name (or raise)."""
  row = app_tables.schema.get(name=schema_name)
  if not row:
    raise ValueError(f"Schema '{schema_name}' not found in the schema table.")
  return row


# ---------------------------------------------------------------------------
# Cached look-ups (config changes are rare – 10 min cache is fine)
# ---------------------------------------------------------------------------

@lru_cache(maxsize=32)
def _cached_structure(schema_name):
  """Return the `structure` simpleObject for a schema (cached)."""
  row = _schema_row(schema_name)
  return row["structure"] or {}


@lru_cache(maxsize=32)
def _cached_field_configs(schema_name, include_excluded=False):
  """
  Return a list of field-config dicts for this schema.

  Each dict includes:
      path, widget_type, layout_group, excluded,
      label_override, view_mode, choices
  """
  row = _schema_row(schema_name)
  # `schema` column in config is a link_multiple – search with list
  configs = app_tables.config.search(schema=[row])

  results = []
  for c in configs:
    if not include_excluded and c["excluded"]:
      continue
    results.append({
      "path":           c["path"],
      "widget_type":    c["widget_type"] or "TextBox",
      "layout_group":   c["layout_group"],
      "excluded":       bool(c["excluded"]),
      "label_override": c["label_override"],
      "view_mode":      c["view_mode"],
      "choices":        c["choices"]            # may be None
    })
  # Sort by path so results are deterministic (renderer can re-order anyway)
  return sorted(results, key=lambda d: d["path"])


# ---------------------------------------------------------------------------
# Public server-callable API
# ---------------------------------------------------------------------------

@anvil.server.callable
def get_schema_structure(schema_name: str):
  """
  Return ONLY the `structure` object for the requested schema.

  Example:
      {
        "layout": [
          {"title": "Document Info", "style": "two-column"},
          ...
        ]
      }
  """
  return {
    "schema": schema_name,
    "retrieved": _now_iso(),
    "structure": _cached_structure(schema_name)
  }


@anvil.server.callable
def get_field_configs(schema_name: str, *, include_excluded: bool = False):
  """
  Return a list of field configuration dicts for the schema.

  Set include_excluded=True if the client needs to know even hidden fields.
  """
  return {
    "schema": schema_name,
    "retrieved": _now_iso(),
    "fields": _cached_field_configs(schema_name, include_excluded)
  }


@anvil.server.callable
def get_full_schema_bundle(schema_name: str, *, include_excluded: bool = False):
  """
  Convenience wrapper: returns structure + field configs together so the
  client can make a single round-trip.

  {
    "schema": "base_lease",
    "retrieved": "2025-05-22T15:45:12Z",
    "structure": {...},
    "fields": [...]
  }
  """
  return {
    "schema": schema_name,
    "retrieved": _now_iso(),
    "structure": _cached_structure(schema_name),
    "fields": _cached_field_configs(schema_name, include_excluded)
  }


# ---------------------------------------------------------------------------
# Admin helpers (optional – not callable from client)
# ---------------------------------------------------------------------------

def _clear_cache():
  """Manually clear the lru_cache layers (use after editing tables)."""
  _cached_structure.cache_clear()
  _cached_field_configs.cache_clear()

