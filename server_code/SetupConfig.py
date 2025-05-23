# ----------------------------------------------------------------------
# seed_base_lease_config()
#   Populate app_tables.config for the "base_lease" schema
#   Safe to re-run (upserts).  Server-side only—no Uplink needed.
# ----------------------------------------------------------------------

def seed_base_lease_config():
  from anvil.tables import app_tables

  # 1️⃣  locate the schema row ------------------------------------------------
  schema_row = app_tables.schema.get(name="base_deed")
  if not schema_row:
    raise RuntimeError("⚠️  'base_lease' schema row not found. "
                       "Create it (with structure JSON) first.")

  # 2️⃣  field definitions ----------------------------------------------------
  #   (path, widget_type, layout_group, excluded)


  ## LEASE FIELDS ##
  # fields = [
  #   # --- Document Info ---
  #   ("state",                              "TextBox",  "Document Info",   False),
  #   ("county",                             "TextBox",  "Document Info",   False),
  #   ("document_number",                    "TextBox",  "Document Info",   False),
  #   ("volume",                             "TextBox",  "Document Info",   False),
  #   ("page",                               "TextBox",  "Document Info",   False),
  #   ("document_type",                      "TextBox",  "Document Info",   False),
  #   ("instrument_date",                    "TextBox",  "Document Info",   False),
  #   ("gross_acres",                        "TextBox",  "Document Info",   False),

  #   # --- Legal Description ---
  #   ("legal_description",                  "TextArea", "Legal Description", False),

  #   # --- Lease Info ---
  #   ("document_details.primary_term.unit",             "TextBox", "Lease Info", False),
  #   ("document_details.primary_term.duration",         "TextBox", "Lease Info", False),
  #   ("document_details.extension_term.unit",           "TextBox", "Lease Info", False),
  #   ("document_details.extension_term.duration",       "TextBox", "Lease Info", False),
  #   ("document_details.addendum",                      "TextBox", "Lease Info", False),
  #   ("document_details.royalty",                       "TextBox", "Lease Info", False),

  #   # --- Analysis ---
  #   ("document_details.open_interest_score",           "TextBox",  "Analysis", False),
  #   ("document_details.open_interest_reasoning",       "TextArea", "Analysis", False),
  #   ("document_details.lease_complexity_reasoning",    "TextArea", "Analysis", False),
  #   ("document_details.lease_complexity_score",        "TextBox",  "Analysis", False),
  #   ("document_details.analysis",                      "TextArea", "Analysis", False),

  #   # --- Explicitly exclude run_config ---
  #   ("run_config",                         "TextBox",  None,       True),
  # ]




  
  fields = [
    # --- Document Info ---
    
    ("volume",                             "TextBox",  "Document Info",   False),
    ("page",                               "TextBox",  "Document Info",   False),
    ("book",                               "TextBox",  "Document Info",   False),
    ("document_number",                    "TextBox",  "Document Info",   False),
    ("document_type",                      "TextBox",  "Document Info",   False),
    ("instrument_date",                    "TextBox",  "Document Info",   False),
    ("file_date",                    "TextBox",  "Document Info",   False),
     ("comments",                    "TextArea",  "Document Info",   False),

    # --- Legal Description ---
    ("legal_description",                  "TextArea", "Legal Description", False),

    # --- Explicitly exclude run_config ---
    ("run_config",                         "TextBox",  None,       True),
  ]

  # 3️⃣  upsert rows ----------------------------------------------------------
  for path, widget_type, layout_group, excluded in fields:

    # link_multiple columns expect a list of rows
    criteria = {"schema": [schema_row], "path": path}

    row = app_tables.config.get(**criteria)

    if row:
      row.update(
        widget_type   = widget_type,
        layout_group  = layout_group,
        excluded      = excluded
      )
    else:
      app_tables.config.add_row(
        schema        = [schema_row],      # ← list !
        path          = path,
        widget_type   = widget_type,
        layout_group  = layout_group,
        excluded      = excluded
      )

  return "✅ base_lease config seeded (rows inserted/updated successfully)."
