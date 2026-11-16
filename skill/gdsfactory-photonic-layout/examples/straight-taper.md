# Example: straight waveguide + taper

## User prompt

> Create a design named `first_chip`. Add a straight waveguide 800 nm wide and 500 µm long, connect a 20 µm taper from 800 nm to 500 nm, check the design, preview it, then export GDS.

## Expected tool sequence

1. `new_design(name="first_chip")`
2. `get_component_schema(type_name="straight")`
3. `create_component(name="wg1", type_name="straight", parameters={"length": "500 um", "width": "800 nm"})`
4. `get_component_schema(type_name="taper")`
5. `create_component(name="tp1", type_name="taper", parameters={"length": "20 um", "width1": "800 nm", "width2": "500 nm"})`
6. `get_component_ports(name="wg1")` and `get_component_ports(name="tp1")`
7. `connect_components` using the matching optical ports (typically `o2` → `o1` after verifying)
8. `check_design`
9. `preview_design` (optional review)
10. `export_gds` and show the annotated PNG

## Expected agent summary

- Design: `first_chip`
- Components: `wg1` (straight), `tp1` (taper)
- Checks passed; GDS/JSON/PNG written under `build/`
- Note: generic PDK prototype only
