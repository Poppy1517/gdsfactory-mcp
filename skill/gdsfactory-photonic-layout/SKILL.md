---
name: gdsfactory-photonic-layout
description: Designs, checks, and exports photonic chip layouts with the gdsfactory MCP server (generic PDK). Use when the user asks to create a PIC layout, build waveguides or MMIs, place grating couplers, route optical ports, run design checks, preview a layout, or export GDS/JSON/PNG. Do not use for foundry tape-out PDK work, full DRC sign-off, or optical simulation.
summary: Agent skill for photonic layout design with gdsfactory MCP—create components, connect and route ports, check designs, and export GDS.
version: 1.0.0
tags:
  - photonics
  - gdsfactory
  - PIC
  - MCP
  - layout
keywords:
  - photonic integrated circuit
  - waveguide
  - MMI
  - grating coupler
  - GDS export
  - optical routing
use_cases:
  - Build a passive splitter tree with MMI and grating couplers
  - Create waveguides, tapers, and bends then route ports
  - Check connectivity and export annotated GDS/JSON/PNG
docs_url: https://github.com/Poppy1517/gdsfactory-mcp
---

# gdsfactory Photonic Layout

Teach the agent how to drive the local **gdsfactory MCP server** to create, edit, check, and export photonic layouts using the generic PDK.

## Prerequisites

1. The buyer must have [Poppy1517/gdsfactory-mcp](https://github.com/Poppy1517/gdsfactory-mcp) installed locally (Python 3.12+, `uv`).
2. The MCP client must register the server (stdio). Example config:

```json
{
  "mcpServers": {
    "gdsfactory": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/gdsfactory-mcp",
        "run",
        "gdsfactory-mcp-server"
      ]
    }
  }
}
```

3. Confirm ~23 tools are visible before designing. If tools are missing, stop and ask the user to fix MCP config (see `references/troubleshooting.md`).

## Scope and hard limits

- **In scope:** passive photonic layout with the allowlisted component set, port connections, Manhattan routing, connectivity/geometry checks, GDS/JSON/PNG export.
- **Out of scope:** foundry PDKs, fab DRC sign-off, optical simulation, active device models beyond what the generic PDK exposes.
- Always state that results use the **generic PDK** and are for learning/prototyping unless the user already knows this.

## Standard workflow (follow in order)

For every completed layout request:

1. **`new_design`** with a clear name. If blocked by unsaved changes, `save_design` first or ask before `discard_unsaved_changes=true`.
2. **`list_component_types`** / **`get_component_schema`** before creating unfamiliar devices. Never invent parameter names.
3. **`create_component`** (preferred) for all 28 allowlisted types. Use `create_straight` / `create_taper` only for legacy µm-only calls.
4. **`place_component`** when absolute placement matters (mirror → rotate CCW → translate).
5. **`get_component_ports`** before connecting. Use real port names (`o1`, `o2`, `o3`, …).
6. Connect with **`connect_components`** (direct snap, moves target) or **`route_components`** (keeps both fixed; optional `waypoints_um`).
7. **`save_design`** early for editable JSON recovery.
8. **`check_design`**. Fix every `severity: "error"` finding before export.
9. **`preview_design`** when the user wants a review-only PNG, or rely on export PNG.
10. **`export_gds`**. Show the annotated PNG path to the user. Do not set `overwrite=true` unless the user explicitly allows replacing existing files.

Read `references/workflow.md` for decision rules (direct vs route, waypoints, overwrite policy).

## Units and parameters

- Bare numbers in generic create/update mean **nm**. Strings like `"500 nm"`, `"0.5 um"`, `"0.5 µm"`, or `{"value": 500, "unit": "nm"}` are accepted.
- Internal storage and placement/routing coordinates are **µm**.
- Parameters ending in `_um` (legacy tools) are always micrometres.
- Details: `references/units-and-parameters.md`.

## Tool quick map

| Goal | Tools |
| --- | --- |
| Inspect | `get_design`, `list_component_types`, `get_component_schema`, `get_technology`, `get_component_ports`, `list_designs`, `check_design` |
| Edit | `new_design`, `create_component`, `create_straight`, `create_taper`, `update_component`, `place_component`, `delete_component`, `rename_component`, `copy_component` |
| Connect | `connect_components`, `route_components`, `disconnect_components` |
| Persist | `save_design`, `load_design`, `preview_design`, `export_gds` |

Full signatures and notes: `references/mcp-tools.md`. Component catalog: `references/components.md`.

## Failure handling

- Failed calls are **atomic**—do not rebuild the whole design after one error.
- Read `error_type`, `error`, and `suggestion`. Correct inputs and retry.
- Common fixes are in `references/troubleshooting.md`.

## Output contract

After finishing a layout (or when the user asks for export), report:

1. **Design name** and whether checks passed.
2. **Component list** (name → type) and **connection count**.
3. **Files written** (JSON / GDS / PNG paths when created).
4. **Caveat:** generic PDK; not foundry-qualified; no optical performance guarantee.
5. Show or link the annotated **PNG** whenever export/preview succeeds.

## Examples

- Straight + taper: `examples/straight-taper.md`
- Bent route with waypoints: `examples/bent-route.md`
- 1550 nm TE 1×4 MMI splitter tree: `examples/mmi-1x4-splitter.md`
