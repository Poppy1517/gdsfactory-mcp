# MCP tools reference

The gdsfactory MCP server exposes **23 tools**. Prefer this map when choosing calls.

## Read-only / inspect

| Tool | Use when |
| --- | --- |
| `get_design` | Need current components, µm dimensions, connections, unsaved flag |
| `list_component_types` | Discover allowlisted types; optional `category` / `status` filters |
| `get_component_schema` | Before create/update: parameter names, units, defaults, limits, `generic_creation_exposed` |
| `get_technology` | Active PDK, layers, cross-section defaults, bend radii |
| `get_component_ports` | Real port names, µm coordinates, orientation degrees, widths, layers |
| `list_designs` | Enumerate valid JSON under `designs/` |
| `check_design` | Connectivity / geometry report before save or export |

## Design and component edits

| Tool | Notes |
| --- | --- |
| `new_design(name, discard_unsaved_changes=false)` | Replaces in-memory design; blocked by unsaved work unless discard |
| `create_component(name, type_name, parameters?)` | Primary creator for all integrated types |
| `create_straight(name, length_um, width_um)` | Legacy; values are micrometres only |
| `create_taper(name, length_um, width1_um, width2_um)` | Legacy; values are micrometres only |
| `update_component(name, parameters)` | Atomic multi-parameter update; same unit rules as create |
| `place_component(name, x_um?, y_um?, rotation_deg?, mirror_x?)` | Mirror → rotate CCW → translate; omitted fields keep prior values |
| `delete_component(name, delete_connections=false)` | Related connections require explicit delete |
| `rename_component(name, new_name)` | Updates connection references atomically |
| `copy_component(name, new_name)` | Copies type/params/placement, not connections; starts overlapping |

## Connections

| Tool | Behavior |
| --- | --- |
| `connect_components(source_component, source_port, target_component, target_port)` | **Direct**: snaps target port onto source; widths must match |
| `route_components(..., cross_section="strip", radius_um?, waypoints_um?)` | **Route**: keeps both devices fixed; optional intermediate `[x, y]` µm waypoints |
| `disconnect_components(component_a, port_a, component_b, port_b)` | Order-independent; preserves components; direct target keeps pre-disconnect placement |

## Persist / preview / export

| Tool | Output |
| --- | --- |
| `save_design(target, overwrite=false)` | Editable JSON only (default under `designs/`) |
| `load_design(path, discard_unsaved_changes=false)` | Loads JSON; blocked by unsaved work unless discard |
| `preview_design(name?, output_dir="previews", show_* , overwrite=false)` | Annotated PNG only |
| `export_gds(name?, output_dir="build", overwrite=false)` | GDS + JSON + annotated PNG; blocked if checks fail |

## Response conventions

- Success: `ok: true`, usually includes `design` and `has_unsaved_changes`.
- Failure: `ok: false` with `error_type`, `error`, `suggestion`.
- Warnings: operation succeeded but needs human attention.
- Failed mutations do not partially apply (atomic).

## Recommended default sequence

`new_design` → `get_component_schema` → `create_component` → `get_component_ports` → `connect_components` / `route_components` → `check_design` → `export_gds` → show PNG.
