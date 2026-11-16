# Units and parameters

## Length values in `create_component` / `update_component`

Accepted forms:

```json
500
"500 nm"
"0.5 um"
"0.5 µm"
{"value": 500, "unit": "nm"}
```

Rules:

1. A bare number defaults to **nanometres (nm)**.
2. `um` and `µm` both mean micrometres.
3. The server stores and reports design geometry in **micrometres**.
4. Length-like fields ending in `_um` on legacy tools are **always micrometres**—do not pass nm into those.
5. Angles such as `rotation_deg` use **degrees**.
6. Dimensionless values (`fill_factor`, refractive indices, counts, `p`, …) are not length-converted.

Example:

```json
{
  "name": "wg1",
  "type_name": "straight",
  "parameters": {
    "length": "500 um",
    "width": "800 nm"
  }
}
```

## Placement and routing coordinates

- `place_component` uses `x_um`, `y_um`, `rotation_deg`, `mirror_x`.
- `route_components` uses `radius_um` and `waypoints_um` as `[x, y]` pairs in micrometres.
- Waypoints are **intermediate** points only. Do not repeat the source/target port coordinates; the server appends real endpoints.

## Schema discipline

1. Call `get_component_schema(type_name)`.
2. Submit only parameters with `generic_creation_exposed: true` (unless using a documented legacy tool).
3. Respect reported limits and defaults.
4. After success, inspect `unit_conversions` in the tool response when present.

## Naming

- Component names must be unique and start with a letter or underscore; letters, digits, and underscores only.
- Prefer short descriptive names: `mmi_stage1`, `gc_out_0`, `wg_in`.
