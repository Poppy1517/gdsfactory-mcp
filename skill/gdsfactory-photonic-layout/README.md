# gdsfactory Photonic Layout (Agensi Skill)

Agent skill that teaches AI clients how to design photonic integrated circuit (PIC) layouts with the local [gdsfactory-mcp](https://github.com/Poppy1517/gdsfactory-mcp) MCP server.

This package is a **Skill**, not a hosted MCP server. Buyers install `gdsfactory-mcp` on their machine, connect it in their MCP client, then load this skill so the agent follows a reliable layout workflow.

## What you get

| Path | Purpose |
| --- | --- |
| `SKILL.md` | Trigger description and step-by-step agent procedure |
| `references/` | Tools, components, units, workflow, troubleshooting |
| `examples/` | Prompt-ready layout scenarios with expected tool sequences |
| `scripts/` | Self-contained helpers for local packaging checks |
| `listing/PRODUCT.md` | Marketplace listing copy for Agensi.io |

## Requirements

- Python **3.12+** and [uv](https://docs.astral.sh/uv/)
- Local clone of [Poppy1517/gdsfactory-mcp](https://github.com/Poppy1517/gdsfactory-mcp)
- An MCP client that supports stdio servers

Install and verify the server:

```bash
git clone https://github.com/Poppy1517/gdsfactory-mcp.git
cd gdsfactory-mcp
uv sync
uv run python -m pytest
```

MCP client config (replace the absolute path):

```json
{
  "mcpServers": {
    "gdsfactory": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/gdsfactory-mcp",
        "run",
        "gdsfactory-mcp-server"
      ]
    }
  }
}
```

## How to use with an agent

1. Connect the gdsfactory MCP server and confirm tools are listed.
2. Install or upload this skill in your agent / Agensi workflow.
3. Ask for a photonic layout, for example:

> Design a 1550 nm TE 1×4 splitter using three 1×2 MMIs and elliptical grating couplers. Use strip waveguides 500 nm wide and Euler bend radius 100 µm. Check the design and export GDS.

The skill steers the agent through schema lookup → create → place/route → check → export, and requires showing the annotated PNG.

## Limits

- Uses the gdsfactory **generic PDK** (learning and prototyping).
- Not a substitute for foundry PDKs, full DRC, or optical simulation.
- Agensi does not host or run the MCP server; local install is required.

## Package for Agensi

From the repository root:

```bash
uv run python skill/gdsfactory-photonic-layout/scripts/package_skill.py
```

This writes `dist/gdsfactory-photonic-layout.zip` with a single top-level skill folder.

## License / source

Skill content accompanies the open-source MCP project at https://github.com/Poppy1517/gdsfactory-mcp.
