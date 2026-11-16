"""Lightweight smoke tests for the existing MCP server (read-only assertions)."""

from __future__ import annotations

from gdsfactory_mcp.design import DesignService
from gdsfactory_mcp.registry import COMPONENT_REGISTRY
from gdsfactory_mcp import server as mcp_server


def test_registry_has_integrated_components() -> None:
    assert len(COMPONENT_REGISTRY) == 28
    assert all(item.status == "integrated" for item in COMPONENT_REGISTRY.values())


def test_mcp_server_registers_expected_tool_count() -> None:
    names = {tool.name for tool in mcp_server.mcp._tool_manager.list_tools()}
    assert len(names) == 23
    assert "create_component" in names
    assert "export_gds" in names


def test_design_service_straight_taper_roundtrip(tmp_path) -> None:
    design = DesignService("smoke_chip")
    design.add_component(
        "wg1",
        "straight",
        {"length": 500.0, "width": 0.8},
    )
    design.add_component(
        "tp1",
        "taper",
        {"length": 20.0, "width1": 0.8, "width2": 0.5},
    )
    assert len(design.spec.components) == 2
    out = tmp_path / "smoke_chip.json"
    design.save_json(out)
    loaded = DesignService("loading")
    loaded.load_json(out)
    assert loaded.spec.name == "smoke_chip"
    assert len(loaded.spec.components) == 2
