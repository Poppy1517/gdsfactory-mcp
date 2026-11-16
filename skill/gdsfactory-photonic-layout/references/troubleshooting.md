# Troubleshooting

## Client does not show tools

1. From the project directory run `uv run gdsfactory-mcp-server` and confirm it starts.
2. Verify the MCP config absolute path to the repo.
3. Ensure `command` is `uv`, or the absolute path from `which uv`.
4. Save config and reconnect/restart the MCP client.
5. Expect about **23** tools when connected.

## `invalid_parameters`

Call `get_component_schema` for that type. Submit only exposed parameters. Length units must be `nm`, `um`, or `µm` (or bare nm numbers).

## `name_conflict`

Component names must be unique. Call `get_design` and choose another name.

## `component_not_found` / `port_not_found`

Call `get_design`, then `get_component_ports`. Do not assume every device has only `o1`/`o2`.

## Direct connection fails

Direct links require connectable on-chip optical ports with matching widths. If placements are fixed or orientation is wrong, use `route_components` instead.

## Route radius too small

Call `get_technology` for the cross-section minimum radius. Increase `radius_um` or omit it to use the default.

## Waypoint / disconnected route errors

Intermediate waypoints only; keep Manhattan segments. Re-check with `check_design` after routing.

## Cannot start or load a design

Unsaved changes are present. Prefer `save_design`. Use `discard_unsaved_changes=true` only with user confirmation.

## `file_conflict`

Default policy preserves existing files. Rename the output or set `overwrite=true` only after explicit confirmation.

## Checks block export

Fix every `severity: "error"` finding in `check_report.findings`. Unexpected same-layer overlaps/crossings block export—move devices, add waypoints, or insert a `crossing`. Warnings need review but do not block export.

Current checks are not foundry DRC and do not prove optical performance.
