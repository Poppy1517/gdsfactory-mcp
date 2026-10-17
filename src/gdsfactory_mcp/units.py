"""Parse public length inputs into the internal micrometre representation."""

import re
from typing import Any

from gdsfactory_mcp.component_schema import get_generic_parameter_units

_LENGTH_PATTERN = re.compile(
    r"^\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)\s*"
    r"(nm|nanometers?|nanometres?|um|µm|μm|micrometers?|micrometres?)\s*$",
    re.IGNORECASE,
)
_NANOMETRE_UNITS = {"nm", "nanometer", "nanometers", "nanometre", "nanometres"}
_MICROMETRE_UNITS = {
    "um", "µm", "μm", "micrometer", "micrometers", "micrometre", "micrometres",
}


def _to_micrometres(value: Any, *, parameter_name: str) -> tuple[float, str]:
    """Convert one supported public quantity and report its interpreted unit."""
    if isinstance(value, bool):
        raise ValueError(f"length parameter '{parameter_name}' cannot be boolean")
    if isinstance(value, int | float):
        return float(value) / 1000.0, "nm (default)"
    if isinstance(value, str):
        match = _LENGTH_PATTERN.fullmatch(value)
        if match is None:
            raise ValueError(
                f"invalid length for '{parameter_name}': {value!r}; use a number "
                "(default nm), '500 nm', '0.5 um', or {'value': 500, 'unit': 'nm'}"
            )
        number = float(match.group(1))
        unit = match.group(2).lower()
    elif isinstance(value, dict):
        if set(value) != {"value", "unit"}:
            raise ValueError(
                f"invalid length object for '{parameter_name}'; expected exactly "
                "{'value': number, 'unit': 'nm' or 'um'}"
            )
        number = value["value"]
        unit = value["unit"]
        if isinstance(number, bool) or not isinstance(number, int | float):
            raise ValueError(f"length value for '{parameter_name}' must be a number")
        if not isinstance(unit, str):
            raise ValueError(f"length unit for '{parameter_name}' must be a string")
        number = float(number)
        unit = unit.strip().lower()
    else:
        raise ValueError(
            f"invalid length for '{parameter_name}'; expected number, unit string, or object"
        )

    if unit in _NANOMETRE_UNITS:
        return number / 1000.0, "nm"
    if unit in _MICROMETRE_UNITS:
        return number, "µm"
    raise ValueError(
        f"unsupported length unit for '{parameter_name}': {unit}; use nm, um, or µm"
    )


def normalize_component_parameters(
    type_name: str,
    parameters: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Normalize exposed length parameters; bare numbers mean nanometres."""
    units = get_generic_parameter_units(type_name)
    normalized = dict(parameters)
    conversions: list[dict[str, Any]] = []
    for name, value in parameters.items():
        if units.get(name) != "length" or value is None:
            continue
        value_um, interpreted_unit = _to_micrometres(value, parameter_name=name)
        normalized[name] = value_um
        conversions.append({
            "parameter": name,
            "input": value,
            "interpreted_unit": interpreted_unit,
            "internal_value_um": value_um,
        })
    return normalized, conversions
