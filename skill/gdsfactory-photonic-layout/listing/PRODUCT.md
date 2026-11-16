# Agensi listing copy (English)

Paste these fields into https://www.agensi.io/dashboard/submit. Keep everything in English.

## Name (≤ 60 characters)

```text
gdsfactory Photonic Layout
```

## Summary (≤ 300 characters)

```text
Design photonic chip layouts with the gdsfactory MCP server: create waveguides and MMIs, route ports, run checks, and export GDS/JSON/PNG using a reliable agent workflow.
```

## Description (Markdown)

```markdown
## What this skill does

Guides your AI agent through photonic integrated circuit (PIC) layout design with the local **gdsfactory MCP server**. It covers component creation, placement, direct port connection and Manhattan routing, design checks, annotated previews, and GDS/JSON/PNG export.

## How it works

1. You install [gdsfactory-mcp](https://github.com/Poppy1517/gdsfactory-mcp) and connect it in your MCP client.
2. Your agent loads this skill when you ask for PIC layouts, waveguides, MMIs, grating couplers, routing, checks, or GDS export.
3. The skill enforces a safe sequence: schema lookup → create → ports → connect/route → check → export, and always surfaces the annotated PNG.

## What's included

- Step-by-step agent procedure (`SKILL.md`)
- Tool, component, unit, workflow, and troubleshooting references
- Ready-to-run example prompts (straight+taper, bent route, 1×4 MMI tree)

## Requirements

- Python 3.12+ and `uv`
- Local gdsfactory-mcp MCP server (stdio)
- An MCP-capable AI client

## Limitations

- Uses the gdsfactory **generic PDK** for learning and prototyping
- Not a foundry PDK, full DRC sign-off, or optical simulator
- Agensi does not host the MCP server; you run it locally
```

## See it in action (700+ characters recommended)

```text
User: Design a 1550 nm TE 1×4 splitter with three 1×2 MMIs and elliptical grating couplers. Strip width 500 nm, Euler bend radius 100 µm. Check and export GDS.

Agent (following this skill):
1. Starts design mmi_1x4_1550_te
2. Reads schemas for mmi1x2 and grating_coupler_elliptical
3. Creates three MMIs plus one input and four output GCs
4. Places devices for a left-to-right two-stage tree
5. Reads real ports, then routes with strip cross-section and 100 µm radius
6. Saves JSON, runs check_design, fixes any blocking errors
7. Exports GDS + JSON + annotated PNG and reports file paths
8. Reminds you the layout uses the generic PDK and is not foundry-qualified

Result: a connected 1×4 splitter tree with check report and preview PNG ready for visual review.
```

## Compatibility note

```text
Requires Python 3.12+, uv, and a local install of Poppy1517/gdsfactory-mcp configured as a stdio MCP server. This skill teaches the agent how to use that server; Agensi does not host it.
```

## Suggested categories / tags / use cases

- Categories (pick up to 3 that exist on Agensi): Engineering, Developer Tools, Science / Research (adjust to the live category list)
- Tags: photonics, gdsfactory, PIC, GDS, MCP, waveguide, MMI
- Use cases: photonic layout drafting, MMI splitter networks, grating-coupler I/O, optical routing, GDS export via AI agents

## Permissions / Needs access to

- **Needs access to:** local gdsfactory MCP server (`gdsfactory-mcp-server`)
- File write under the project (`designs/`, `previews/`, `build/`) when the MCP server runs
- No network APIs and no secrets required by the skill itself

## Limitations & FAQ (optional fields)

**Limitations**

- Generic PDK only; not tape-out ready
- Connectivity/geometry checks ≠ foundry DRC
- Export success ≠ optical performance

**FAQ**

- *Do I need gdsfactory installed?* Yes—via the gdsfactory-mcp project (`uv sync`).
- *Can Agensi run the MCP server for me?* No. Install and connect it locally, then use this skill.
- *Does this modify the MCP server?* No. The skill is instructions + references + examples only.
