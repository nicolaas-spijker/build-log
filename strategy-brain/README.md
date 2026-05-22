# strategy-brain — a template

The brain template from the SignalRoads Build Log case study, "Building
and maintaining a marketing brain on top of Claude."

A brain is the layer that carries your positioning, your customer, and
your judgment, so an AI agent inherits them on every task instead of
guessing. It is one file plus a folder:

- `CLAUDE.md` — the always-loaded file. Short. Read at the start of every
  session by Claude Code and Cowork.
- `docs/` — the depth. Read on demand when a task calls for it. Holds
  reference (style, positioning) and your workflows.

## How to use it

1. Copy `CLAUDE.md` and the `docs/` folder into the root of your project.
2. Fill `CLAUDE.md` from your strategy. If your strategy is not written
   down yet, write it first. The brain is downstream of it.
3. Fill the `docs/` files, or delete the ones you do not need.
4. Sharpen it over time, every time you catch the agent guessing.

If you work in Cowork rather than a terminal, point a project at the
folder you copied these into. It loads `CLAUDE.md` the same way.

Full walkthrough: the case study on SignalRoads.
