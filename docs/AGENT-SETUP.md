# Agent Setup Guide — Collaborative Document Editor

This document covers setup, configuration, and verification of the four coding agents used in this project: **OpenCode**, **OpenAI Codex**, **Cursor**, and **Claude Code** (reserved).

---

## 1. Agent Overview

| Agent | Role | Status |
|-------|------|--------|
| **OpenCode** | Primary agent — orchestrates implementation, dispatches subagents | Active |
| **OpenAI Codex** | Review & rescue agent — reviews completed work, intervenes on failures | Active |
| **Cursor** | IDE-integrated agent — interactive coding, real-time collaboration | Active |
| **Claude Code** | Not currently in use | Reserved |

---

## 2. OpenCode Setup

### MCP Configuration

Config location: `<repo-root>/opencode.json`

OpenCode loads MCP servers and plugins from the project-level `opencode.json`. The current configuration includes:

- **Figma MCP** — `framelink-figma-mcp` via npx
- **Graphify MCP** — local Python MCP server for knowledge graph queries
- **Superpowers plugin** — auto-loaded from GitHub

### Skill Directory

Location: `<repo-root>/.opencode/skills/`

Each skill is a subdirectory containing a `SKILL.md` file. Skills are discovered and listed in the agent's available skills list.

### Verification

```bash
# Verify OpenCode sees the MCPs — check opencode.json is valid
cat opencode.json | python -m json.tool > /dev/null && echo "Config valid"

# Verify Graphify MCP server module loads
./tools/graphify/.venv/Scripts/python.exe -c "from graphify.serve import _load_graph; print('MCP module OK')"

# Verify skills directory structure
ls .opencode/skills/

# Verify superpowers — ask OpenCode:
# "Tell me about your superpowers" or "List available skills"
```

---

## 3. Codex Setup

### MCP Configuration

Config location: `<repo-root>/.codex/mcp.json`

Codex reads MCP server definitions from `.codex/mcp.json` at the project root. The format follows the standard `mcpServers` schema.

### Hook Configuration

Config location: `<repo-root>/.codex/hooks.json`

Contains a `PreToolUse` hook for Graphify integration — when a knowledge graph exists, Codex is reminded to consult it before running bash commands.

### Feature Flags

Config location: `<repo-root>/.codex/config.toml`

Requires `multi_agent = true` under `[features]` for Graphify's parallel subagent extraction.

### Skill Discovery

Codex discovers skills via:
1. Built-in skills catalog
2. The `skill` tool for listing and loading
3. Skills installed at `.codex/skills/` (local) or `~/.codex/skills/` (global)

To install Superpowers in Codex, use the plugin interface:
```
/plugins
```
Search for "Superpowers" and select **Install Plugin**.

Alternatively, for project-local skills, copy from `tools/superpowers/skills/` to `.codex/skills/`.

### Verification

```bash
# Verify MCP config
python -m json.tool .codex/mcp.json > /dev/null && echo "Config valid"

# Verify hooks
python -m json.tool .codex/hooks.json > /dev/null && echo "Hooks valid"

# Verify multi-agent is enabled
grep "multi_agent" .codex/config.toml

# In Codex, run:
# /graphify .
# $graphify query "show the auth flow" --graph graphify-out/graph.json
```

---

## 4. Cursor Setup

### MCP Configuration

Config location: `<repo-root>/.cursor/mcp.json`

Cursor reads MCP server definitions from `.cursor/mcp.json` at the project root. The format follows the standard `mcpServers` schema, compatible with Claude Desktop format.

### Skill/Plugin Discovery

Cursor supports skills/plugins via its built-in marketplace:
```
/add-plugin superpowers
```

Or search for "superpowers" in the plugin marketplace UI.

Cursor also respects `.cursorrules` files for project-level instructions, and `.cursor/rules/` for always-applied rules.

### Verification

```bash
# Verify MCP config
python -m json.tool .cursor/mcp.json > /dev/null && echo "Config valid"

# In Cursor, ask:
# "List available MCP tools" or "Read the graphify graph"
```

---

## 5. Claude Code (Reserved)

Claude Code is **not currently in use** for this project but is reserved for future use.

When activated, setup would involve:
- Config: `~/.claude/CLAUDE.md` or project `CLAUDE.md`
- MCP: `~/.claude/mcp.json` or project `.mcp.json`
- Skills: `~/.claude/skills/` directory
- Graphify install: `graphify claude install`

---

## 6. Graphify Setup

Graphify turns the codebase into a queryable knowledge graph with community detection and an interactive HTML visualizer.

### Install

Graphify is pre-installed in a project-local venv:

```powershell
# Already done — re-run if needed:
cd tools/graphify
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install ".[mcp]"
```

### Build the Knowledge Graph

Before the MCP server can serve queries, the graph must be built:

```powershell
# From repo root:
./tools/graphify/.venv/Scripts/python.exe -m graphify . --no-viz
```

This creates `graphify-out/graph.json`, `graphify-out/GRAPH_REPORT.md`, and `graphify-out/graph.html`.

Or use the CLI shortcut (if `graphify` is on PATH):

```bash
graphify . --no-viz
```

### Exclusions

The `.graphifyignore` file at the repo root excludes build artifacts, external dependencies, and tool directories from graph ingestion.

### MCP Server

The MCP server exposes the graph as tools: `query_graph`, `get_node`, `get_neighbors`, `get_community`, `god_nodes`, `graph_stats`, `shortest_path`.

Manual start:

```bash
./tools/graphify/.venv/Scripts/python.exe -m graphify.serve ./graphify-out/graph.json
```

### Verification Prompt

```
List the modules in `backend/app/features/core/` and their public symbols.
What are the god nodes in the graph?
Show me the path between the auth module and the documents module.
```

---

## 7. Figma MCP Setup

The Figma MCP (`framelink-figma-mcp`) provides design token extraction from Figma files.

### Token Setup

Set the `FIGMA_API_KEY` environment variable before starting any agent:

**Windows (PowerShell):**
```powershell
$env:FIGMA_API_KEY = "figd_..."
```

**Unix (bash/zsh):**
```bash
export FIGMA_API_KEY="figd_..."
```

For persistent setup, add to your shell profile (`~/.bashrc`, `~/.zshrc`, or `$PROFILE`):

```bash
export FIGMA_API_KEY="figd_your_personal_access_token"
```

Generate a token at: https://www.figma.com/developers/api#authentication

> **SECURITY:** NEVER commit the API key to version control. Use environment variables or a `.env` file (which is gitignored). The `opencode.json` uses `${FIGMA_API_KEY}` to reference the env var.

### Configured Figma File

- **Figma Community Kit:** https://www.figma.com/community/file/1359075236113343829
- **File ID:** `1359075236113343829`

The MCP auto-discovers files. To specify a file explicitly, set `FIGMA_FILE_ID` env var.

### Verification Prompt

```
Fetch the colors from the Figma file ID 1359075236113343829.
List all design tokens available in the Figma file.
```

---

## 8. Superpowers Skills Installation

The Superpowers methodology provides composable skills for systematic software development.

### Required Skills

| Skill | Purpose |
|-------|---------|
| `using-superpowers` | Introduction to the skills system |
| `brainstorming` | Socratic design refinement |
| `writing-plans` | Detailed implementation plans |
| `executing-plans` | Batch execution with checkpoints |
| `test-driven-development` | RED-GREEN-REFACTOR cycle |
| `requesting-code-review` | Pre-review checklist |
| `receiving-code-review` | Responding to feedback |
| `verification-before-completion` | Ensure it's actually fixed |
| `using-git-worktrees` | Parallel development branches |
| `finishing-a-development-branch` | Merge/PR decision workflow |
| `subagent-driven-development` | Fast iteration with two-stage review |
| `dispatching-parallel-agents` | Concurrent subagent workflows |
| `systematic-debugging` | 4-phase root cause process |

### Install via Script

**Windows (PowerShell):**
```powershell
.\scripts\install_skills.ps1
```

Re-run with `-Force` to update from upstream:
```powershell
.\scripts\install_skills.ps1 -Force
```

**Unix (bash):**
```bash
bash scripts/install_skills.sh
```

Re-run with `--force` to update from upstream:
```bash
bash scripts/install_skills.sh --force
```

### What the Script Does

1. Clones `obra/superpowers` into `tools/superpowers/` (or updates if already cloned with `--force`)
2. Copies each required skill from `tools/superpowers/skills/<name>/` to `.opencode/skills/<name>/`
3. Each skill is a folder containing `SKILL.md` + reference files
4. Idempotent — skips already-installed skills unless `--force` is used

### Auto-Loading (OpenCode)

The `opencode.json` includes the plugin declaration for auto-loading:

```json
{
  "plugin": ["superpowers@git+https://github.com/obra/superpowers.git"]
}
```

With this, OpenCode auto-discovers all Superpowers skills on startup.

### Verification Prompt

```
Use the `verification-before-completion` skill to review whether all P1 exit criteria are met.
List the available superpowers skills and describe what each one does.
```

---

## 9. Quick Verification Checklist

Run these after initial setup:

```powershell
# 1. Config files are valid JSON
python -m json.tool opencode.json > $null && echo "opencode.json OK"
python -m json.tool .cursor/mcp.json > $null && echo ".cursor/mcp.json OK"
python -m json.tool .codex/mcp.json > $null && echo ".codex/mcp.json OK"
python -m json.tool .codex/hooks.json > $null && echo ".codex/hooks.json OK"

# 2. Graphify MCP module loads
./tools/graphify/.venv/Scripts/python.exe -c "from graphify.serve import _load_graph; print('Graphify MCP OK')"

# 3. Skills directory exists
if (Test-Path ".opencode/skills") { echo "Skills directory exists" }

# 4. Superpowers repo cloned
if (Test-Path "tools/superpowers/.git") { echo "Superpowers repo cloned" }
```

---

## 10. Known Issues / Troubleshooting

### Graphify

| Issue | Resolution |
|-------|------------|
| Graph is empty | Run `./tools/graphify/.venv/Scripts/python.exe -m graphify .` first to build the graph |
| `graphify-out/` doesn't exist | The MCP server requires a pre-built graph — run extraction first |
| `ModuleNotFoundError: graphify` | Re-run `./tools/graphify/.venv/Scripts/python.exe -m pip install ".[mcp]"` |
| MCP server won't start | Ensure `graphify-out/graph.json` exists and is valid JSON |
| Leiden clustering fails on Python 3.13+ | Install `graspologic` from source or use Python 3.12 for graphify |

### Figma MCP

| Issue | Resolution |
|-------|------------|
| `FIGMA_API_KEY` not found | Set env var: `$env:FIGMA_API_KEY = "figd_..."` |
| Token invalid | Regenerate at https://www.figma.com/developers/api#authentication |
| File not accessible | Ensure the Figma file is in a team the token has access to |
| npx fails to find `figma-mcp` | Run `npx -y figma-mcp --help` to verify package exists |

### Superpowers Skills

| Issue | Resolution |
|-------|------------|
| Skills not showing in agent | Run `scripts/install_skills.ps1` to copy skills |
| Plugin not loading | Verify `opencode.json` has the `plugin` array, restart OpenCode |
| Old skills after update | Run install script with `-Force` flag |
| `using-git-worktrees` fails on Windows | Git worktrees require administrator privileges on Windows |

### General

| Issue | Resolution |
|-------|------------|
| MCP server connection refused | Ensure the server process is running; check for port conflicts |
| Token committed to repo | Rotate immediately; use env vars going forward |
| Multiple agent configs out of sync | Run verification checklist to identify drift |
| Codex `multi_agent = true` not working | Check `.codex/config.toml` syntax; requires Codex v1.0+ |
