"""Smoke tests for MCP server import and tool registration."""

from gdsfactory_mcp import server


def test_server_module_importable() -> None:
    assert server.__file__ is not None
    assert hasattr(server, "mcp")


def test_server_registers_twenty_three_tools() -> None:
    tools = server.mcp._tool_manager._tools
    assert len(tools) == 23
    for name in (
        "check_design",
        "create_component",
        "export_gds",
        "get_technology",
        "list_component_types",
        "new_design",
        "route_components",
    ):
        assert name in tools
