# Allowlisted components

All types below are **integrated** with `create_component` / `update_component` in the current gdsfactory MCP release. Always call `get_component_schema` before using a type you have not used in this session.

## Waveguide, bend, crossing

| `type_name` | Common name |
| --- | --- |
| `straight` | Straight waveguide |
| `bend_euler` | Euler bend |
| `bend_s` | S-bend |
| `crossing` | Waveguide crossing |

## Tapers

| `type_name` | Common name |
| --- | --- |
| `taper` | Linear taper |
| `taper_adiabatic` | Adiabatic taper |

## Couplers

| `type_name` | Common name |
| --- | --- |
| `coupler` | Directional coupler |
| `coupler_straight` | Straight coupler section |
| `coupler_ring` | Ring coupler |

## MMI

| `type_name` | Common name |
| --- | --- |
| `mmi1x2` | MMI 1×2 |
| `mmi2x2` | MMI 2×2 |

## Resonators

| `type_name` | Common name |
| --- | --- |
| `ring_single` | Single-bus ring |
| `ring_double` | Double-bus ring |
| `coupled_ring_chain` | Four-ring CROW |
| `disk` | Disk resonator |

## Grating couplers

| `type_name` | Common name |
| --- | --- |
| `grating_coupler_elliptical` | Elliptical focusing GC |
| `grating_coupler_rectangular` | Rectangular GC |

## Edge couplers

| `type_name` | Common name |
| --- | --- |
| `edge_coupler_silicon` | Silicon edge coupler |
| `edge_coupler_array` | Edge coupler array |

## Spirals and delay lines

| `type_name` | Common name |
| --- | --- |
| `spiral` | Spiral waveguide |
| `spiral_racetrack_fixed_length` | Fixed-length racetrack spiral |
| `delay_snake_sbend` | Snake delay with S-bends |

## Circuits / composites

| `type_name` | Common name |
| --- | --- |
| `mzi` | Mach–Zehnder interferometer |
| `mzi2x2_2x2_phase_shifter` | Heater MZI 2×2 |
| `straight_heater_metal` | Thermo-optic phase shifter |
| `splitter_tree` | Splitter tree |
| `dbr` | Distributed Bragg reflector |
| `loop_mirror` | Loop mirror |

## Categories for `list_component_types`

- `waveguide_bend_crossing`
- `taper`
- `coupler`
- `mmi`
- `resonator`
- `grating_coupler`
- `edge_coupler`
- `spiral_delay`
- `circuit`

## Cross-section references

Managed names include `strip`, `rib`, and `slot`. Prefer `get_technology` / route profile data over guessing bend radii.
