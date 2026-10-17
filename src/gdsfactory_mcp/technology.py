"""Central access to the active PDK, layers, and safe cross-sections."""

from typing import Any

import gdsfactory as gf

from gdsfactory_mcp.registry import REGISTERED_REFERENCES

TECHNOLOGY_SOURCE = {
    "provider": "gdsfactory",
    "pdk_factory": "gdsfactory.gpdk.PDK",
    "qualification": "generic demonstration PDK; not foundry-qualified",
    "selection": "activated explicitly by gdsfactory_mcp.technology.activate_technology",
}


def activate_technology() -> Any:
    """Activate and return the one PDK selected by this project."""
    gf.gpdk.PDK.activate()
    return gf.get_active_pdk()


def _layer_data(layer_name: str) -> dict[str, Any]:
    layer_index = int(gf.get_layer(layer_name))
    layer_info = gf.kcl.layout.get_info(layer_index)
    return {
        "name": layer_name,
        "layer": int(layer_info.layer),
        "datatype": int(layer_info.datatype),
    }


def get_cross_section_profile(name: str) -> dict[str, Any]:
    """Return managed defaults and layers for one safe cross-section."""
    allowed = REGISTERED_REFERENCES["cross_section"]
    if name not in allowed:
        choices = ", ".join(sorted(allowed))
        raise ValueError(
            f"unregistered cross_section reference: {name}; available references: {choices}"
        )
    activate_technology()
    cross_section = gf.get_cross_section(name)
    sections = []
    for section in cross_section.sections:
        layer = _layer_data(str(section.layer))
        sections.append({
            "width_um": float(section.width),
            "offset_um": float(section.offset),
            "layer": layer,
        })
    return {
        "name": name,
        "default_width_um": float(cross_section.width),
        "default_radius_um": (
            float(cross_section.radius) if cross_section.radius is not None else None
        ),
        "minimum_radius_um": (
            float(cross_section.radius_min)
            if cross_section.radius_min is not None
            else None
        ),
        "sections": sections,
        "source": {
            "pdk": gf.get_active_pdk().name,
            "cross_section_registry_key": name,
            "runtime_object": f"gdsfactory.get_cross_section('{name}')",
        },
    }


def get_technology_profile() -> dict[str, Any]:
    """Describe the selected PDK, all declared layers, and safe cross-sections."""
    pdk = activate_technology()
    layers = [
        _layer_data(name)
        for name in pdk.layers.__members__
    ]
    cross_sections = [
        get_cross_section_profile(name)
        for name in sorted(REGISTERED_REFERENCES["cross_section"])
    ]
    return {
        "active_pdk": {
            "name": pdk.name,
            "version": getattr(pdk, "version", None),
        },
        "technology_source": TECHNOLOGY_SOURCE,
        "layers": layers,
        "layer_count": len(layers),
        "safe_cross_sections": cross_sections,
        "safe_cross_section_count": len(cross_sections),
        "units": {
            "internal_length": "µm",
            "public_bare_length_default": "nm",
            "gds_database_unit_um": float(gf.kcl.dbu),
        },
        "limitations": [
            "The generic PDK is for development and demonstration, not tapeout.",
            "Foundry-specific layer maps and design rules are not configured.",
            "Only explicitly registered cross-sections are exposed to MCP inputs.",
        ],
    }
