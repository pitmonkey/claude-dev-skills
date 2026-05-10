---
name: skill-manager-help
description: Use when the user wants to know what commands the skill-manager MCP supports or what to ask Claude to do with it.
---

This is a reference for the user. Print the table below exactly as-is and nothing else — no commentary, no follow-up questions, no offers to help.

# skill-manager MCP — Command Reference

## Skills

| Tool | What it does | Example phrase |
|------|-------------|----------------|
| `list_skills` | List all registered skills, optionally filtered by tags | "show me my skills" |
| `get_skill` | Read the full markdown content of a skill | "show me the content of the commit skill" |
| `load_skill` | Activate a skill by adding it to CLAUDE.md | "load the grill-me skill" / "activate the commit skill" |
| `unload_skill` | Deactivate a skill by removing it from CLAUDE.md | "unload the grill-me skill" |
| `search_skills` | Keyword search across name, description, and tags | "search my skills for anything about git" |

## Subagents

| Tool | What it does | Example phrase |
|------|-------------|----------------|
| `list_agents` | List all registered subagents | "list my subagents" / "show agents" |
| `get_agent` | Read the full markdown content of a subagent | "show me the content of the python-pro agent" |
| `load_agent` | Activate a subagent by adding it to CLAUDE.md and .claude/agents/ | "load the code-reviewer agent" |
| `unload_agent` | Deactivate a subagent by removing it from CLAUDE.md and .claude/agents/ | "unload the code-reviewer agent" |
| `search_agents` | Keyword search across name, description, and tags | "search agents for testing" |

## Universal

| Tool | What it does | Example phrase |
|------|-------------|----------------|
| `install_skill` | Clone a git repo and register each skill/agent found in it | "install skills from https://github.com/..." |
| `update_skill` | Pull latest changes for a single git-backed skill or agent | "update the commit skill" |
| `update_skills` | Pull latest changes for all git-backed skills and agents at once | "update all my community skills" |
| `check_updates` | Dry run — see which skills/agents have upstream changes without pulling | "check if any skills have updates" |
| `migrate` | Bootstrap existing skill directories that predate the registry | "migrate my existing skills" |
