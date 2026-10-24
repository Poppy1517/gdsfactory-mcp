"""Registry and component schema smoke tests."""

import pytest

from gdsfactory_mcp.component_schema import get_component_schema_data
from gdsfactory_mcp.registry import (
    ALLOWED_COMPONENT_TYPES,
    COMPONENT_REGISTRY,
    get_component_definition,
)


def test_registry_has_integrated_core_types() -> None:
    for type_name in (
        "straight",
        "mmi1x2",
        "grating_coupler_elliptical",
        "splitter_tree",
        "bend_euler",
    ):
        definition = get_component_definition(type_name)
        assert definition.status == "integrated"
        assert type_name in ALLOWED_COMPONENT_TYPES
        assert type_name in COMPONENT_REGISTRY


def test_registry_rejects_unknown_type() -> None:
    with pytest.raises(ValueError, match="unsupported component type"):
        get_component_definition("not_a_real_component")


def test_mmi1x2_schema_exposes_width() -> None:
    schema = get_component_schema_data("mmi1x2")
    assert schema["generic_creation_available"] is True
    interface = schema["generic_creation_interface"]
    assert interface is not None
    parameter_names = {item["name"] for item in interface["parameters"]}
    assert "width" in parameter_names
