# Example: fixed devices with bent route

## User prompt

> Place two straight waveguides apart and route them with a strip cross-section and 100 µm bend radius. Use waypoints if needed so the path stays Manhattan. Check and export.

## Expected tool sequence

1. `new_design(name="bent_route")`
2. Create two `straight` components with `create_component`
3. `place_component` each device at distinct `(x_um, y_um)` so they do not overlap
4. `get_component_ports` for both ends
5. `route_components(..., cross_section="strip", radius_um=100, waypoints_um=[...])` if a simple route is insufficient
6. `check_design` — if `disconnected_route_geometry` appears, adjust waypoints
7. `export_gds` and show the PNG

## Notes for the agent

- Prefer route over direct connect when placements must stay fixed.
- Waypoints are intermediate only.
- Call `get_technology` if the chosen radius may be below the strip minimum.
