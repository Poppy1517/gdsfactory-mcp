# Example: 1550 nm TE 1×4 MMI splitter network

## User prompt

> Use gdsfactory MCP to design a 1550 nm TE 1×4 splitter: three 1×2 MMIs in a two-stage tree, one input and four output elliptical grating couplers. Use generic PDK defaults, strip width 500 nm, Euler bend radius 100 µm. Light left-to-right; stage MMI pitch 400 µm; second-stage vertical spacing 254 µm; output gratings spaced 127 µm vertically.

## Expected tool sequence

1. `new_design(name="mmi_1x4_1550_te")`
2. `get_component_schema` for `mmi1x2` and `grating_coupler_elliptical` (and any waveguide/bend helpers used)
3. Create three `mmi1x2` instances for the tree
4. Create one input + four output `grating_coupler_elliptical` instances
5. `place_component` to match the requested pitches and left-to-right flow
6. `get_component_ports` for every connection endpoint
7. `route_components` (preferred) or `connect_components` between stages with strip/`radius_um=100`
8. `save_design("mmi_1x4_1550_te")`
9. `check_design` and fix errors
10. `export_gds` and display the annotated PNG

## Expected agent summary

- Two-stage 1×2 MMI tree feeding four elliptical GCs
- Checks passed or remaining warnings listed
- Export paths for GDS/JSON/PNG
- Caveat: generic PDK; not foundry-qualified; no optical performance claim
