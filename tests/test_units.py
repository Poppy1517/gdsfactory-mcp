"""Unit tests for public length parsing."""

import pytest

from gdsfactory_mcp.units import normalize_component_parameters


def test_bare_number_defaults_to_nanometres() -> None:
    normalized, conversions = normalize_component_parameters(
        "straight",
        {"length": 500, "width": 500},
    )
    assert normalized["length"] == pytest.approx(0.5)
    assert normalized["width"] == pytest.approx(0.5)
    assert conversions[0]["interpreted_unit"] == "nm (default)"


def test_string_micrometre_unit() -> None:
    normalized, conversions = normalize_component_parameters(
        "straight",
        {"length": "20 um", "width": "0.5 µm"},
    )
    assert normalized["length"] == pytest.approx(20.0)
    assert normalized["width"] == pytest.approx(0.5)
    assert {item["interpreted_unit"] for item in conversions} == {"µm"}


def test_object_nanometre_unit() -> None:
    normalized, conversions = normalize_component_parameters(
        "straight",
        {"length": {"value": 500, "unit": "nm"}, "width": {"value": 500, "unit": "nm"}},
    )
    assert normalized["length"] == pytest.approx(0.5)
    assert conversions[0]["internal_value_um"] == pytest.approx(0.5)


def test_invalid_length_string_raises() -> None:
    with pytest.raises(ValueError, match="invalid length"):
        normalize_component_parameters("straight", {"length": "500 mm"})
