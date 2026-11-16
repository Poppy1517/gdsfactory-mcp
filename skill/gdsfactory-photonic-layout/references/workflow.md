# Layout workflow decisions

## Direct connect vs route

Use **`connect_components`** (direct) when:

- Ports face each other and should abut.
- Matching widths are already guaranteed.
- Moving the **target** component is acceptable.

Use **`route_components`** when:

- Both devices must keep fixed placements.
- You need bends, Manhattan jogs, or clearances.
- Widths differ and a waveguide/taper route is required.
- You need `waypoints_um` to avoid crossings or obstacles.

Never guess port names—call `get_component_ports` first.

## Waypoints

- Provide only intermediate `[x, y]` points in µm.
- Adjacent segments should be Manhattan (horizontal or vertical).
- Do not duplicate the real source/target port coordinates.
- If `check_design` reports `disconnected_route_geometry`, fix waypoints or placements and re-route.

## Placement order

`place_component` applies transforms in this order:

1. Mirror across local X (`mirror_x`)
2. Counter-clockwise rotation (`rotation_deg`)
3. Translation (`x_um`, `y_um`)

Omit a field to keep its previous value.

## Save / overwrite policy

1. Prefer `save_design` early so the editable JSON can be recovered.
2. Never set `overwrite=true` unless the user explicitly allows replacing named files.
3. Unsaved changes block `new_design` / `load_design`—save or ask before discarding.

## Completion checklist

Before telling the user the layout is done:

1. `check_design` with no error-severity findings
2. `export_gds` succeeded (or explain why export is blocked)
3. Annotated PNG path is shown
4. Generic-PDK caveat is stated once
