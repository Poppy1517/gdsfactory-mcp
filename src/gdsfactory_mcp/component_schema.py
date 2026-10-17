"""Read-only parameter schemas for allowlisted gdsfactory component factories."""

import inspect
from typing import Any

import gdsfactory as gf

from gdsfactory_mcp.registry import get_component_definition

_MICROMETRE_TOKENS = (
    "length", "width", "gap", "radius", "spacing", "offset",
    "wavelength", "period", "pitch", "xmin", "dx", "dy",
)
_DEGREE_NAMES = {
    "angle", "angular_step", "fiber_angle", "taper_angle", "wrap_angle_deg",
}
_REFERENCE_TYPES = ("ComponentSpec", "CrossSectionSpec", "LayerSpec", "Port")

_KNOWN_LIMITS = {
    ("straight", "length"): "greater than 0",
    ("straight", "npoints"): "integer greater than or equal to 2",
    ("straight", "width"): "greater than 0 when provided",
    ("taper", "length"): "greater than 0",
    ("taper", "width1"): "greater than 0",
    ("taper", "width2"): "greater than 0 when provided",
    ("taper_adiabatic", "width1"): "greater than 0 and different from width2",
    ("taper_adiabatic", "width2"): "greater than 0 and different from width1",
    ("taper_adiabatic", "length"): "fixed to 0 for automatic calculation",
    ("taper_adiabatic", "alpha"): "greater than 0 and at most 100",
    ("taper_adiabatic", "wavelength"): "greater than 0 and at most 100",
    ("taper_adiabatic", "npoints"): "integer from 20 to 5000",
    ("taper_adiabatic", "max_length"): "greater than 0 and at most 10000",
    ("taper_adiabatic", "cross_section"): "fixed to strip for the built-in effective-index model",
    ("bend_euler", "radius"): "greater than 0 when provided",
    ("bend_euler", "angle"): "-360 to 360 degrees, excluding 0",
    ("bend_euler", "p"): "between 0 and 1",
    ("bend_euler", "width"): "greater than 0 when provided",
    ("bend_s", "size"): "exposed as scalar aliases size_x and size_y",
    ("bend_s", "width"): "greater than 0 when provided",
    ("crossing", "arm"): "fixed safe crossing_arm with exposed scalar aliases",
    ("mmi1x2", "width"): "greater than 0 when provided",
    ("mmi1x2", "width_taper"): "greater than 0",
    ("mmi1x2", "length_taper"): "greater than 0",
    ("mmi1x2", "length_mmi"): "greater than 0",
    ("mmi1x2", "width_mmi"): "at least 2 * width_taper + gap_mmi",
    ("mmi1x2", "gap_mmi"): "greater than or equal to 0",
    ("mmi2x2", "width"): "greater than 0 when provided",
    ("mmi2x2", "width_taper"): "greater than 0",
    ("mmi2x2", "length_taper"): "greater than 0",
    ("mmi2x2", "length_mmi"): "greater than 0",
    ("mmi2x2", "width_mmi"): "at least 2 * width_taper + gap_mmi",
    ("mmi2x2", "gap_mmi"): "greater than or equal to 0",
    ("coupler", "gap"): "greater than 0 and less than dy",
    ("coupler", "length"): "greater than 0",
    ("coupler", "dy"): "greater than gap",
    ("coupler", "dx"): "greater than 0",
    ("coupler_straight", "length"): "greater than 0",
    ("coupler_straight", "gap"): "greater than 0",
    ("coupler_ring", "gap"): "greater than 0",
    ("coupler_ring", "radius"): "greater than 0 when provided",
    ("coupler_ring", "length_x"): "greater than 0",
    ("ring_single", "gap"): "greater than 0",
    ("ring_single", "radius"): "greater than 0 when provided",
    ("ring_single", "length_x"): "greater than 0",
    ("ring_single", "length_y"): "greater than 0",
    ("ring_double", "gap"): "greater than 0",
    ("ring_double", "gap_top"): "greater than 0 when provided",
    ("ring_double", "gap_bot"): "greater than 0 when provided",
    ("ring_double", "radius"): "greater than 0 when provided",
    ("ring_double", "length_x"): "greater than 0",
    ("ring_double", "length_y"): "greater than 0",
    ("coupled_ring_chain", "radius"): "greater than 0",
    ("disk", "radius"): "greater than 0",
    ("disk", "gap"): "greater than 0",
    ("disk", "wrap_angle_deg"): "greater than 0 and at most 360 degrees",
    ("disk", "parity"): "1 or -1",
    ("grating_coupler_elliptical", "polarization"): "te or tm",
    ("grating_coupler_elliptical", "taper_angle"): "greater than 0 and less than 180 degrees",
    ("grating_coupler_elliptical", "fiber_angle"): "-90 to 90 degrees",
    ("grating_coupler_elliptical", "n_periods"): "integer from 1 to 1000",
    ("grating_coupler_elliptical", "neff"): "greater than nclad",
    ("grating_coupler_rectangular", "polarization"): "te or tm",
    ("grating_coupler_rectangular", "fill_factor"): "greater than 0 and less than 1",
    ("grating_coupler_rectangular", "fiber_angle"): "-90 to 90 degrees",
    ("grating_coupler_rectangular", "n_periods"): "integer from 1 to 1000",
    ("edge_coupler_silicon", "length"): "greater than 0",
    ("edge_coupler_silicon", "width1"): "greater than 0",
    ("edge_coupler_silicon", "width2"): "greater than 0",
    ("edge_coupler_array", "n"): "integer from 1 to 256",
    ("edge_coupler_array", "pitch"): "greater than 0",
    ("spiral", "length"): "greater than 0; length of each main straight section, not total path length",
    ("spiral", "spacing"): "greater than 0",
    ("spiral", "n_loops"): "even integer from 2 to 100",
    ("spiral_racetrack_fixed_length", "length"): "greater than 0; target total path length must be feasible for the other geometry",
    ("spiral_racetrack_fixed_length", "in_out_port_spacing"): "greater than 0",
    ("spiral_racetrack_fixed_length", "n_straight_sections"): "even integer from 2 to 100",
    ("spiral_racetrack_fixed_length", "min_radius"): "greater than 0 when provided",
    ("spiral_racetrack_fixed_length", "min_spacing"): "greater than 0",
    ("delay_snake_sbend", "length"): "greater than length1 + length4; gdsfactory 9.51.0 may report a different actual physical length",
    ("delay_snake_sbend", "length1"): "greater than or equal to 0",
    ("delay_snake_sbend", "length4"): "greater than or equal to 0",
    ("delay_snake_sbend", "radius"): "greater than 0",
    ("delay_snake_sbend", "waveguide_spacing"): "greater than 0",
    ("delay_snake_sbend", "sbend_xsize"): "greater than 0",
    ("mzi", "delta_length"): "-10000 to 10000 micrometres; sign selects the longer arm",
    ("mzi", "length_y"): "greater than 0",
    ("mzi", "length_x"): "greater than 0",
    ("mzi", "nbends"): "integer from 2 to 100",
    ("mzi", "min_length"): "greater than 0",
    ("mzi2x2_2x2_phase_shifter", "delta_length"): "-10000 to 10000 micrometres; use 0 for a balanced MZI",
    ("mzi2x2_2x2_phase_shifter", "length_y"): "greater than 0",
    ("mzi2x2_2x2_phase_shifter", "length_x"): "greater than 0",
    ("mzi2x2_2x2_phase_shifter", "nbends"): "integer from 2 to 100",
    ("mzi2x2_2x2_phase_shifter", "min_length"): "greater than 0",
    ("straight_heater_metal", "length"): "greater than 0",
    ("straight_heater_metal", "heater_taper_length"): "greater than 0",
    ("splitter_tree", "noutputs"): "power of 2 from 2 to 256",
    ("splitter_tree", "spacing"): "exposed as positive scalar aliases spacing_x and spacing_y",
    ("splitter_tree", "bend_s_xsize"): "greater than 0 when provided",
    ("dbr", "w1"): "greater than 0 and different from w2",
    ("dbr", "w2"): "greater than 0 and different from w1",
    ("dbr", "l1"): "greater than 0",
    ("dbr", "l2"): "greater than 0",
    ("dbr", "n"): "integer from 1 to 10000",
    ("dbr", "straight_length"): "greater than 0",
    ("loop_mirror", "component"): "fixed safe mmi1x2 with exposed scalar aliases",
    ("loop_mirror", "bend90"): "fixed to gdsfactory bend_euler",
}

_CURRENT_MCP_INTERFACES = {
    "straight": {
        "tool": "create_straight",
        "parameters": [
            {"name": "name", "type": "string", "unit": None, "limits": "valid unique component name"},
            {"name": "length_um", "type": "number", "unit": "µm", "limits": "greater than 0"},
            {"name": "width_um", "type": "number", "unit": "µm", "limits": "greater than 0"},
        ],
    },
    "taper": {
        "tool": "create_taper",
        "parameters": [
            {"name": "name", "type": "string", "unit": None, "limits": "valid unique component name"},
            {"name": "length_um", "type": "number", "unit": "µm", "limits": "greater than 0"},
            {"name": "width1_um", "type": "number", "unit": "µm", "limits": "greater than 0"},
            {"name": "width2_um", "type": "number", "unit": "µm", "limits": "greater than 0"},
        ],
    },
}

_GENERIC_MCP_INTERFACES = {
    "straight": {
        "tool": "create_component",
        "parameters": [
            {"name": "length", "type": "number", "default": 10.0, "unit": "µm", "limits": "greater than 0"},
            {"name": "width", "type": "number", "default": 0.5, "unit": "µm", "limits": "greater than 0"},
            {"name": "cross_section", "type": "registered_reference", "default": None, "unit": None, "limits": "registered cross_section: rib, slot, or strip"},
        ],
    },
    "taper": {
        "tool": "create_component",
        "parameters": [
            {"name": "length", "type": "number", "default": 10.0, "unit": "µm", "limits": "greater than 0"},
            {"name": "width1", "type": "number", "default": 0.5, "unit": "µm", "limits": "greater than 0"},
            {"name": "width2", "type": "number", "default": 0.5, "unit": "µm", "limits": "greater than 0"},
            {"name": "cross_section", "type": "registered_reference", "default": None, "unit": None, "limits": "registered cross_section: rib, slot, or strip"},
        ],
    },
    "bend_euler": {
        "tool": "create_component",
        "parameters": [
            {"name": "radius", "type": "number", "default": 10.0, "unit": "µm", "limits": "greater than 0"},
            {"name": "angle", "type": "number", "default": 90.0, "unit": "degree", "limits": "-360 to 360, excluding 0"},
            {"name": "p", "type": "number", "default": 0.5, "unit": None, "limits": "0 to 1"},
            {"name": "width", "type": "number", "default": 0.5, "unit": "µm", "limits": "greater than 0"},
            {"name": "cross_section", "type": "registered_reference", "default": None, "unit": None, "limits": "registered cross_section: rib, slot, or strip"},
        ],
    },
    "bend_s": {
        "tool": "create_component",
        "parameters": [
            {"name": "size_x", "type": "number", "default": 11.0, "unit": "µm", "limits": "greater than 0"},
            {"name": "size_y", "type": "number", "default": 1.8, "unit": "µm", "limits": "-10000 to 10000, excluding 0"},
            {"name": "width", "type": "number", "default": 0.5, "unit": "µm", "limits": "greater than 0"},
            {"name": "cross_section", "type": "registered_reference", "default": None, "unit": None, "limits": "registered cross_section: rib, slot, or strip"},
        ],
    },
    "crossing": {
        "tool": "create_component",
        "parameters": [
            {"name": "r1", "type": "number", "default": 3.0, "unit": "µm", "limits": "greater than r2"},
            {"name": "r2", "type": "number", "default": 1.1, "unit": "µm", "limits": "greater than 0 and less than r1"},
            {"name": "arm_width", "type": "number", "default": 1.2, "unit": "µm", "limits": "greater than 0"},
            {"name": "arm_length", "type": "number", "default": 3.4, "unit": "µm", "limits": "greater than 0"},
            {"name": "cross_section", "type": "registered_reference", "default": None, "unit": None, "limits": "registered cross_section: rib, slot, or strip"},
        ],
    },
    "taper_adiabatic": {
        "tool": "create_component",
        "parameters": [
            {"name": "width1", "type": "number", "default": 0.5, "unit": "µm", "limits": "greater than 0 and different from width2"},
            {"name": "width2", "type": "number", "default": 5.0, "unit": "µm", "limits": "greater than 0 and different from width1"},
            {"name": "alpha", "type": "number", "default": 1.0, "unit": None, "limits": "greater than 0 and at most 100"},
            {"name": "wavelength", "type": "number", "default": 1.55, "unit": "µm", "limits": "greater than 0 and at most 100"},
            {"name": "npoints", "type": "integer", "default": 200, "unit": "count", "limits": "20 to 5000"},
            {"name": "max_length", "type": "number", "default": 200.0, "unit": "µm", "limits": "greater than 0 and at most 10000"},
        ],
        "fixed_parameters": {
            "length": 0,
            "cross_section": "strip",
            "neff_w": "built-in neff_TE1550SOI_220nm",
        },
    },
    "mmi1x2": {
        "tool": "create_component",
        "parameters": [
            {"name": "width", "type": "number", "default": 0.5, "unit": "µm", "limits": "greater than 0"},
            {"name": "width_taper", "type": "number", "default": 1.0, "unit": "µm", "limits": "greater than 0"},
            {"name": "length_taper", "type": "number", "default": 10.0, "unit": "µm", "limits": "greater than 0"},
            {"name": "length_mmi", "type": "number", "default": 5.5, "unit": "µm", "limits": "greater than 0"},
            {"name": "width_mmi", "type": "number", "default": 2.5, "unit": "µm", "limits": "at least 2 * width_taper + gap_mmi"},
            {"name": "gap_mmi", "type": "number", "default": 0.25, "unit": "µm", "limits": "greater than or equal to 0"},
            {"name": "cross_section", "type": "registered_reference", "default": None, "unit": None, "limits": "registered cross_section: rib, slot, or strip"},
        ],
        "fixed_parameters": {"taper": "gdsfactory taper", "straight": "gdsfactory straight"},
    },
    "mmi2x2": {
        "tool": "create_component",
        "parameters": [
            {"name": "width", "type": "number", "default": 0.5, "unit": "µm", "limits": "greater than 0"},
            {"name": "width_taper", "type": "number", "default": 1.0, "unit": "µm", "limits": "greater than 0"},
            {"name": "length_taper", "type": "number", "default": 10.0, "unit": "µm", "limits": "greater than 0"},
            {"name": "length_mmi", "type": "number", "default": 5.5, "unit": "µm", "limits": "greater than 0"},
            {"name": "width_mmi", "type": "number", "default": 2.5, "unit": "µm", "limits": "at least 2 * width_taper + gap_mmi"},
            {"name": "gap_mmi", "type": "number", "default": 0.25, "unit": "µm", "limits": "greater than or equal to 0"},
            {"name": "cross_section", "type": "registered_reference", "default": None, "unit": None, "limits": "registered cross_section: rib, slot, or strip"},
        ],
        "fixed_parameters": {"taper": "gdsfactory taper", "straight": "gdsfactory straight"},
    },
    "coupler": {
        "tool": "create_component",
        "parameters": [
            {"name": "gap", "type": "number", "default": 0.236, "unit": "µm", "limits": "greater than 0 and less than dy"},
            {"name": "length", "type": "number", "default": 20.0, "unit": "µm", "limits": "greater than 0"},
            {"name": "dy", "type": "number", "default": 4.0, "unit": "µm", "limits": "greater than gap"},
            {"name": "dx", "type": "number", "default": 10.0, "unit": "µm", "limits": "greater than 0"},
            {"name": "cross_section", "type": "registered_reference", "default": None, "unit": None, "limits": "registered cross_section: rib, slot, or strip"},
        ],
        "fixed_parameters": {"bend": "gdsfactory bend_s", "allow_min_radius_violation": False},
    },
    "coupler_straight": {
        "tool": "create_component",
        "parameters": [
            {"name": "length", "type": "number", "default": 10.0, "unit": "µm", "limits": "greater than 0"},
            {"name": "gap", "type": "number", "default": 0.27, "unit": "µm", "limits": "greater than 0"},
            {"name": "cross_section", "type": "registered_reference", "default": None, "unit": None, "limits": "registered cross_section: rib, slot, or strip"},
        ],
    },
    "coupler_ring": {
        "tool": "create_component",
        "parameters": [
            {"name": "gap", "type": "number", "default": 0.2, "unit": "µm", "limits": "greater than 0"},
            {"name": "radius", "type": "number", "default": 10.0, "unit": "µm", "limits": "greater than 0"},
            {"name": "length_x", "type": "number", "default": 4.0, "unit": "µm", "limits": "greater than 0"},
            {"name": "cross_section", "type": "registered_reference", "default": None, "unit": None, "limits": "registered cross_section: rib, slot, or strip"},
            {"name": "cross_section_bend", "type": "registered_reference", "default": None, "unit": None, "limits": "registered cross_section: rib, slot, or strip"},
        ],
        "fixed_parameters": {"bend": "gdsfactory bend_euler", "straight": "gdsfactory straight", "length_extension": None},
    },
    "ring_single": {
        "tool": "create_component",
        "parameters": [
            {"name": "gap", "type": "number", "default": 0.2, "unit": "µm", "limits": "greater than 0"},
            {"name": "radius", "type": "number", "default": 10.0, "unit": "µm", "limits": "greater than 0"},
            {"name": "length_x", "type": "number", "default": 4.0, "unit": "µm", "limits": "greater than 0"},
            {"name": "length_y", "type": "number", "default": 0.6, "unit": "µm", "limits": "greater than 0"},
            {"name": "cross_section", "type": "registered_reference", "default": None, "unit": None, "limits": "registered cross_section: rib, slot, or strip"},
        ],
        "fixed_parameters": {"bend": "gdsfactory bend_euler", "straight": "gdsfactory straight", "coupler_ring": "gdsfactory coupler_ring", "length_extension": None},
    },
    "ring_double": {
        "tool": "create_component",
        "parameters": [
            {"name": "gap", "type": "number", "default": 0.2, "unit": "µm", "limits": "greater than 0"},
            {"name": "gap_top", "type": "number or null", "default": None, "unit": "µm", "limits": "greater than 0 when provided"},
            {"name": "gap_bot", "type": "number or null", "default": None, "unit": "µm", "limits": "greater than 0 when provided"},
            {"name": "radius", "type": "number", "default": 10.0, "unit": "µm", "limits": "greater than 0"},
            {"name": "length_x", "type": "number", "default": 0.01, "unit": "µm", "limits": "greater than 0"},
            {"name": "length_y", "type": "number", "default": 0.01, "unit": "µm", "limits": "greater than 0"},
            {"name": "cross_section", "type": "registered_reference", "default": None, "unit": None, "limits": "registered cross_section: rib, slot, or strip"},
        ],
        "fixed_parameters": {"bend": "gdsfactory bend_euler", "straight": "gdsfactory straight", "coupler_ring": "gdsfactory coupler_ring", "coupler_ring_top": None, "length_extension": None},
    },
    "coupled_ring_chain": {
        "tool": "create_component",
        "parameters": [
            {"name": "radius", "type": "number", "default": 10.0, "unit": "µm", "limits": "greater than 0"},
            {"name": "waveguide_width", "type": "number", "default": 0.45, "unit": "µm", "limits": "greater than 0"},
            {"name": "gap_input", "type": "number", "default": 0.151, "unit": "µm", "limits": "greater than 0"},
            {"name": "gap_12", "type": "number", "default": 0.493, "unit": "µm", "limits": "greater than 0"},
            {"name": "gap_23", "type": "number", "default": 0.587, "unit": "µm", "limits": "greater than 0"},
            {"name": "gap_34", "type": "number", "default": 0.493, "unit": "µm", "limits": "greater than 0"},
            {"name": "gap_output", "type": "number", "default": 0.151, "unit": "µm", "limits": "greater than 0"},
            {"name": "coupling_length", "type": "number", "default": 0.01, "unit": "µm", "limits": "greater than 0"},
            {"name": "vertical_straight_length", "type": "number", "default": 0.01, "unit": "µm", "limits": "greater than 0"},
            {"name": "include_electrodes", "type": "boolean", "default": True, "unit": None, "limits": "true or false"},
            {"name": "pad_width", "type": "number", "default": 22.0, "unit": "µm", "limits": "greater than 0; schematic because the paper does not disclose pad dimensions"},
            {"name": "pad_height", "type": "number", "default": 28.0, "unit": "µm", "limits": "greater than 0; schematic because the paper does not disclose pad dimensions"},
            {"name": "metal_width", "type": "number", "default": 2.0, "unit": "µm", "limits": "greater than 0; schematic because the paper does not disclose metal width"},
        ],
        "fixed_parameters": {
            "ring_count": 4,
            "cross_section": "parameterized gdsfactory rib",
            "factory": "gdsfactory ring_crow",
            "ports": ["input", "through", "drop", "add"],
            "electrode_note": "GSG geometry is schematic; pad and metal dimensions are not disclosed in the paper",
        },
    },
    "disk": {
        "tool": "create_component",
        "parameters": [
            {"name": "radius", "type": "number", "default": 10.0, "unit": "µm", "limits": "greater than 0"},
            {"name": "gap", "type": "number", "default": 0.2, "unit": "µm", "limits": "greater than 0"},
            {"name": "wrap_angle_deg", "type": "number", "default": 180.0, "unit": "degree", "limits": "greater than 0 and at most 360"},
            {"name": "parity", "type": "integer", "default": 1, "unit": None, "limits": "1 or -1"},
            {"name": "cross_section", "type": "registered_reference", "default": None, "unit": None, "limits": "registered cross_section: rib, slot, or strip"},
        ],
    },
    "grating_coupler_elliptical": {
        "tool": "create_component",
        "parameters": [
            {"name": "polarization", "type": "string", "default": "te", "unit": None, "limits": "te or tm"},
            {"name": "taper_length", "type": "number", "default": 16.6, "unit": "µm", "limits": "greater than 0"},
            {"name": "taper_angle", "type": "number", "default": 40.0, "unit": "degree", "limits": "greater than 0 and less than 180"},
            {"name": "wavelength", "type": "number", "default": 1.554, "unit": "µm", "limits": "greater than 0"},
            {"name": "fiber_angle", "type": "number", "default": 15.0, "unit": "degree", "limits": "-90 to 90"},
            {"name": "grating_line_width", "type": "number", "default": 0.343, "unit": "µm", "limits": "greater than 0"},
            {"name": "neff", "type": "number", "default": 2.638, "unit": None, "limits": "greater than nclad"},
            {"name": "nclad", "type": "number", "default": 1.443, "unit": None, "limits": "greater than 0 and less than neff"},
            {"name": "n_periods", "type": "integer", "default": 30, "unit": "count", "limits": "1 to 1000"},
            {"name": "big_last_tooth", "type": "boolean", "default": False, "unit": None, "limits": "true or false"},
            {"name": "slab_xmin", "type": "number", "default": -1.0, "unit": "µm", "limits": "-10000 to 10000"},
            {"name": "slab_offset", "type": "number", "default": 2.0, "unit": "µm", "limits": "greater than 0"},
            {"name": "spiked", "type": "boolean", "default": True, "unit": None, "limits": "true or false"},
            {"name": "cross_section", "type": "registered_reference", "default": None, "unit": None, "limits": "registered cross_section: rib, slot, or strip"},
        ],
        "fixed_parameters": {"layer_slab": "SLAB150"},
    },
    "grating_coupler_rectangular": {
        "tool": "create_component",
        "parameters": [
            {"name": "n_periods", "type": "integer", "default": 20, "unit": "count", "limits": "1 to 1000"},
            {"name": "period", "type": "number", "default": 0.75, "unit": "µm", "limits": "greater than 0"},
            {"name": "fill_factor", "type": "number", "default": 0.5, "unit": None, "limits": "greater than 0 and less than 1"},
            {"name": "width_grating", "type": "number", "default": 11.0, "unit": "µm", "limits": "greater than 0"},
            {"name": "length_taper", "type": "number", "default": 150.0, "unit": "µm", "limits": "greater than 0"},
            {"name": "polarization", "type": "string", "default": "te", "unit": None, "limits": "te or tm"},
            {"name": "wavelength", "type": "number", "default": 1.55, "unit": "µm", "limits": "greater than 0"},
            {"name": "fiber_angle", "type": "number", "default": 15.0, "unit": "degree", "limits": "-90 to 90"},
            {"name": "slab_xmin", "type": "number", "default": -1.0, "unit": "µm", "limits": "-10000 to 10000"},
            {"name": "slab_offset", "type": "number", "default": 1.0, "unit": "µm", "limits": "greater than 0"},
            {"name": "cross_section", "type": "registered_reference", "default": None, "unit": None, "limits": "registered cross_section: rib, slot, or strip"},
        ],
        "fixed_parameters": {"taper": "gdsfactory taper", "layer_slab": "SLAB150", "layer_grating": None},
    },
    "edge_coupler_silicon": {
        "tool": "create_component",
        "parameters": [
            {"name": "length", "type": "number", "default": 100.0, "unit": "µm", "limits": "greater than 0"},
            {"name": "width1", "type": "number", "default": 0.5, "unit": "µm", "limits": "greater than 0"},
            {"name": "width2", "type": "number", "default": 0.2, "unit": "µm", "limits": "greater than 0"},
            {"name": "cross_section", "type": "registered_reference", "default": None, "unit": None, "limits": "registered cross_section: rib, slot, or strip"},
        ],
        "fixed_parameters": {
            "with_two_ports": True,
            "port_names": ["o1", "o2"],
            "port_types": ["optical", "edge_coupler"],
        },
    },
    "edge_coupler_array": {
        "tool": "create_component",
        "parameters": [
            {"name": "n", "type": "integer", "default": 5, "unit": "count", "limits": "1 to 256"},
            {"name": "pitch", "type": "number", "default": 127.0, "unit": "µm", "limits": "greater than 0"},
            {"name": "x_reflection", "type": "boolean", "default": False, "unit": None, "limits": "true or false"},
            {"name": "length", "type": "number", "default": 100.0, "unit": "µm", "limits": "greater than 0"},
            {"name": "width1", "type": "number", "default": 0.5, "unit": "µm", "limits": "greater than 0"},
            {"name": "width2", "type": "number", "default": 0.2, "unit": "µm", "limits": "greater than 0"},
            {"name": "cross_section", "type": "registered_reference", "default": None, "unit": None, "limits": "registered cross_section: rib, slot, or strip"},
            {"name": "include_text", "type": "boolean", "default": True, "unit": None, "limits": "true or false"},
        ],
        "fixed_parameters": {
            "edge_coupler": "safe edge_coupler_silicon adapter",
            "text": "text_rectangular when include_text is true; otherwise none",
            "text_offset": [10, 20],
            "text_rotation": 0,
        },
    },
    "spiral": {
        "tool": "create_component",
        "parameters": [
            {"name": "length", "type": "number", "default": 100.0, "unit": "µm", "limits": "greater than 0; main straight-section length, not total path length"},
            {"name": "spacing", "type": "number", "default": 3.0, "unit": "µm", "limits": "greater than 0"},
            {"name": "n_loops", "type": "integer", "default": 6, "unit": "count", "limits": "even integer from 2 to 100"},
            {"name": "cross_section", "type": "registered_reference", "default": None, "unit": None, "limits": "registered cross_section: rib, slot, or strip"},
        ],
        "fixed_parameters": {
            "bend": "gdsfactory bend_euler",
            "straight": "gdsfactory straight",
        },
    },
    "spiral_racetrack_fixed_length": {
        "tool": "create_component",
        "parameters": [
            {"name": "length", "type": "number", "default": 1000.0, "unit": "µm", "limits": "greater than 0; target total path length must be geometrically feasible"},
            {"name": "in_out_port_spacing", "type": "number", "default": 150.0, "unit": "µm", "limits": "greater than 0"},
            {"name": "n_straight_sections", "type": "integer", "default": 8, "unit": "count", "limits": "even integer from 2 to 100"},
            {"name": "min_radius", "type": "number or null", "default": None, "unit": "µm", "limits": "greater than 0 when provided"},
            {"name": "min_spacing", "type": "number", "default": 5.0, "unit": "µm", "limits": "greater than 0"},
            {"name": "cross_section", "type": "registered_reference", "default": None, "unit": None, "limits": "registered cross_section: rib, slot, or strip"},
            {"name": "cross_section_s", "type": "registered_reference", "default": None, "unit": None, "limits": "registered cross_section: rib, slot, or strip"},
        ],
        "fixed_parameters": {
            "straight": "gdsfactory straight",
            "bend": "gdsfactory bend_circular",
            "bend_s": "gdsfactory bend_s",
        },
    },
    "delay_snake_sbend": {
        "tool": "create_component",
        "parameters": [
            {"name": "length", "type": "number", "default": 100.0, "unit": "µm", "limits": "greater than length1 + length4; actual physical length may differ in gdsfactory 9.51.0"},
            {"name": "length1", "type": "number", "default": 0.0, "unit": "µm", "limits": "greater than or equal to 0"},
            {"name": "length4", "type": "number", "default": 0.0, "unit": "µm", "limits": "greater than or equal to 0"},
            {"name": "radius", "type": "number", "default": 5.0, "unit": "µm", "limits": "greater than 0"},
            {"name": "waveguide_spacing", "type": "number", "default": 5.0, "unit": "µm", "limits": "greater than 0"},
            {"name": "sbend_xsize", "type": "number", "default": 100.0, "unit": "µm", "limits": "greater than 0"},
            {"name": "cross_section", "type": "registered_reference", "default": None, "unit": None, "limits": "registered cross_section: rib, slot, or strip"},
        ],
        "fixed_parameters": {
            "bend": "gdsfactory bend_euler",
            "sbend": "gdsfactory bend_s",
        },
    },
    "mzi": {
        "tool": "create_component",
        "parameters": [
            {"name": "delta_length", "type": "number", "default": 10.0, "unit": "µm", "limits": "-10000 to 10000; sign selects the longer arm"},
            {"name": "length_y", "type": "number", "default": 2.0, "unit": "µm", "limits": "greater than 0"},
            {"name": "length_x", "type": "number", "default": 0.1, "unit": "µm", "limits": "greater than 0"},
            {"name": "nbends", "type": "integer", "default": 2, "unit": "count", "limits": "2 to 100"},
            {"name": "mirror_bot", "type": "boolean", "default": False, "unit": None, "limits": "true or false"},
            {"name": "min_length", "type": "number", "default": 0.01, "unit": "µm", "limits": "greater than 0"},
            {"name": "cross_section", "type": "registered_reference", "default": None, "unit": None, "limits": "registered cross_section: rib, slot, or strip"},
        ],
        "fixed_parameters": {
            "bend": "gdsfactory bend_euler",
            "straight": "gdsfactory straight",
            "straight_y": None,
            "straight_x_top": None,
            "straight_x_bot": None,
            "splitter": "gdsfactory mmi1x2",
            "combiner": None,
            "with_splitter": True,
            "port_names": "built-in mmi1x2 port mapping",
            "cross_section_x_top": None,
            "cross_section_x_bot": None,
            "add_optical_ports_arms": False,
            "auto_rename_ports": True,
            "auto_detect_port_names": False,
        },
    },
    "mzi2x2_2x2_phase_shifter": {
        "tool": "create_component",
        "parameters": [
            {"name": "delta_length", "type": "number", "default": 10.0, "unit": "µm", "limits": "-10000 to 10000; use 0 for a balanced MZI"},
            {"name": "length_y", "type": "number", "default": 2.0, "unit": "µm", "limits": "greater than 0"},
            {"name": "length_x", "type": "number", "default": 200.0, "unit": "µm", "limits": "greater than 0"},
            {"name": "nbends", "type": "integer", "default": 2, "unit": "count", "limits": "2 to 100"},
            {"name": "mirror_bot", "type": "boolean", "default": False, "unit": None, "limits": "true or false"},
            {"name": "min_length", "type": "number", "default": 0.01, "unit": "µm", "limits": "greater than 0"},
            {"name": "cross_section", "type": "registered_reference", "default": None, "unit": None, "limits": "registered cross_section: rib, slot, or strip"},
        ],
        "fixed_parameters": {
            "splitter": "gdsfactory mmi2x2",
            "combiner": "gdsfactory mmi2x2",
            "heated_arm": "gdsfactory straight_heater_metal",
            "optical_ports": ["o1", "o2", "o3", "o4"],
            "electrical_ports": ["e1", "e2", "e3", "e4", "e5", "e6", "e7", "e8"],
            "routing_limit": "electrical port routing is not yet supported by connect_components",
        },
    },
    "straight_heater_metal": {
        "tool": "create_component",
        "parameters": [
            {"name": "length", "type": "number", "default": 320.0, "unit": "µm", "limits": "greater than 0"},
            {"name": "with_undercut", "type": "boolean", "default": False, "unit": None, "limits": "true or false"},
            {"name": "heater_taper_length", "type": "number", "default": 5.0, "unit": "µm", "limits": "greater than 0"},
            {"name": "cross_section", "type": "registered_reference", "default": None, "unit": None, "limits": "registered cross_section: rib, slot, or strip"},
        ],
        "fixed_parameters": {
            "heater_cross_section": "generic PDK metal heater definition",
            "via_stacks": "generic PDK heater contact stacks",
            "electrical_routing": "not yet supported by connect_components",
            "process_note": "heater width and fabrication layers require the target foundry PDK",
        },
    },
    "splitter_tree": {
        "tool": "create_component",
        "parameters": [
            {"name": "noutputs", "type": "integer", "default": 4, "unit": "count", "limits": "power of 2 from 2 to 256"},
            {"name": "spacing_x", "type": "number", "default": 90.0, "unit": "µm", "limits": "greater than 0"},
            {"name": "spacing_y", "type": "number", "default": 50.0, "unit": "µm", "limits": "greater than 0"},
            {"name": "bend_s_xsize", "type": "number or null", "default": None, "unit": "µm", "limits": "greater than 0 when provided"},
            {"name": "cross_section", "type": "registered_reference", "default": None, "unit": None, "limits": "registered cross_section: rib, slot, or strip"},
        ],
        "fixed_parameters": {
            "coupler": "gdsfactory mmi1x2",
            "bend_s": "gdsfactory bend_s",
            "spacing": "constructed from spacing_x and spacing_y",
        },
    },
    "dbr": {
        "tool": "create_component",
        "parameters": [
            {"name": "w1", "type": "number", "default": 0.45, "unit": "µm", "limits": "greater than 0 and different from w2"},
            {"name": "w2", "type": "number", "default": 0.55, "unit": "µm", "limits": "greater than 0 and different from w1"},
            {"name": "l1", "type": "number", "default": 0.159, "unit": "µm", "limits": "greater than 0"},
            {"name": "l2", "type": "number", "default": 0.159, "unit": "µm", "limits": "greater than 0"},
            {"name": "n", "type": "integer", "default": 10, "unit": "count", "limits": "1 to 10000"},
            {"name": "straight_length", "type": "number", "default": 0.01, "unit": "µm", "limits": "greater than 0"},
            {"name": "cross_section", "type": "registered_reference", "default": None, "unit": None, "limits": "registered cross_section: rib, slot, or strip"},
        ],
        "fixed_parameters": {
            "external_ports": ["o1"],
            "port_behavior": "one-port reflective termination in gdsfactory 9.51.0",
        },
    },
    "loop_mirror": {
        "tool": "create_component",
        "parameters": [
            {"name": "width", "type": "number", "default": 0.5, "unit": "µm", "limits": "greater than 0"},
            {"name": "width_taper", "type": "number", "default": 1.0, "unit": "µm", "limits": "greater than 0"},
            {"name": "length_taper", "type": "number", "default": 10.0, "unit": "µm", "limits": "greater than 0"},
            {"name": "length_mmi", "type": "number", "default": 5.5, "unit": "µm", "limits": "greater than 0"},
            {"name": "width_mmi", "type": "number", "default": 2.5, "unit": "µm", "limits": "at least 2 * width_taper + gap_mmi"},
            {"name": "gap_mmi", "type": "number", "default": 0.25, "unit": "µm", "limits": "greater than or equal to 0"},
            {"name": "cross_section", "type": "registered_reference", "default": None, "unit": None, "limits": "registered cross_section: rib, slot, or strip"},
        ],
        "fixed_parameters": {
            "component": "safe gdsfactory mmi1x2 adapter",
            "bend90": "gdsfactory bend_euler",
            "external_ports": ["o1"],
            "port_behavior": "one-port reflective termination",
        },
    },
}


def get_generic_parameter_units(type_name: str) -> dict[str, str]:
    """Return public semantic units for safely exposed generic parameters."""
    interface = _GENERIC_MCP_INTERFACES.get(type_name)
    if interface is None:
        return {}
    return {
        item["name"]: (
            "length"
            if item.get("unit") == "µm"
            else "degree"
            if item.get("unit") == "degree"
            else "count"
            if item.get("unit") == "count"
            else "dimensionless"
        )
        for item in interface["parameters"]
    }


def _public_generic_interface(type_name: str) -> dict[str, Any] | None:
    """Add explicit public-input unit rules without mutating the registry."""
    interface = _GENERIC_MCP_INTERFACES.get(type_name)
    if interface is None:
        return None
    public = {
        key: value
        for key, value in interface.items()
        if key != "parameters"
    }
    public["parameters"] = []
    for parameter in interface["parameters"]:
        item = dict(parameter)
        if item.get("unit") == "µm":
            item["semantic_unit"] = "length"
            item["accepted_input_units"] = ["nm", "um", "µm"]
            item["default_input_unit_for_bare_numbers"] = "nm"
            item["internal_storage_unit"] = "µm"
            item["default_note"] = (
                "The displayed default is an internal µm factory default used when "
                "the parameter is omitted; an explicitly supplied bare number is nm."
            )
        elif item.get("unit") == "degree":
            item["semantic_unit"] = "angle"
        elif item.get("unit") == "count":
            item["semantic_unit"] = "count"
        else:
            item["semantic_unit"] = "dimensionless"
        public["parameters"].append(item)
    return public


def _annotation_text(annotation: Any) -> str | None:
    if annotation is inspect.Parameter.empty:
        return None
    if isinstance(annotation, str):
        return annotation
    return inspect.formatannotation(annotation)


def _json_default(value: Any) -> Any:
    if value is inspect.Parameter.empty:
        return None
    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, tuple | list):
        return [_json_default(item) for item in value]
    if callable(value):
        return {"registered_reference": getattr(value, "__name__", type(value).__name__)}
    return str(value)


def _unit(parameter_name: str) -> str | None:
    if parameter_name.startswith("n_") or parameter_name in {
        "n", "npoints", "nbends", "nloops",
    }:
        return "count"
    if parameter_name in _DEGREE_NAMES or parameter_name.endswith("_angle"):
        return "degree"
    if any(token in parameter_name for token in _MICROMETRE_TOKENS):
        return "µm"
    return None


def _parameter_kind(annotation: str | None) -> str:
    text = annotation or ""
    if any(reference_type in text for reference_type in _REFERENCE_TYPES):
        return "reference"
    if "tuple" in text or "list" in text or "dict" in text:
        return "structured"
    return "scalar"


def _limits(type_name: str, parameter_name: str, annotation: str | None) -> str:
    known = _KNOWN_LIMITS.get((type_name, parameter_name))
    if known:
        return known
    kind = _parameter_kind(annotation)
    if kind == "reference":
        return "generic creation will accept registered references only"
    if annotation and "bool" in annotation:
        return "true or false"
    return "component-specific limit not yet registered"


def get_component_schema_data(type_name: str) -> dict[str, Any]:
    """Return a JSON-compatible schema for one allowlisted component type."""
    definition = get_component_definition(type_name)
    factory = getattr(gf.components, definition.factory_name)
    signature = inspect.signature(factory)
    generic_interface = _GENERIC_MCP_INTERFACES.get(type_name)
    exposed_names = {
        item["name"] for item in generic_interface["parameters"]
    } if generic_interface else set()
    parameters = []
    for parameter in signature.parameters.values():
        annotation = _annotation_text(parameter.annotation)
        parameters.append({
            "name": parameter.name,
            "type": annotation,
            "required": parameter.default is inspect.Parameter.empty,
            "default": _json_default(parameter.default),
            "unit": _unit(parameter.name),
            "kind": _parameter_kind(annotation),
            "limits": _limits(type_name, parameter.name, annotation),
            "generic_creation_exposed": parameter.name in exposed_names,
        })

    return {
        "type_name": definition.type_name,
        "name_zh": definition.name_zh,
        "common_name": definition.common_name,
        "category": definition.category,
        "factory_name": definition.factory_name,
        "status": definition.status,
        "generic_creation_available": generic_interface is not None,
        "factory_parameters": parameters,
        "generic_creation_interface": _public_generic_interface(type_name),
        "current_mcp_interface": _CURRENT_MCP_INTERFACES.get(type_name),
        "unit_policy": {
            "length_inputs": ["nm", "um", "µm"],
            "bare_length_number_unit": "nm",
            "internal_length_unit": "µm",
            "angles": "degree",
            "dimensionless_parameters": "not converted",
            "saved_design_files": "internal values remain µm and are not reinterpreted",
        },
    }

