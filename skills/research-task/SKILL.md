---
name: research-task
description: Use the research-analyst subagent to research a topic, search the internet, and produce a comprehensive markdown write-up with references.
allowed-tools: [Agent, Read, Write, Edit, Glob, Grep, WebFetch, WebSearch]
---

# Research Task

You are coordinating a deep research task. Your job is to:
1. Identify the research topic from the user's request (the argument(s) passed to this command, or the most recent user message if no argument was provided).
2. Delegate the research to the `voltagent-research:research-analyst` subagent.
3. Validate and clean the output before saving.
4. Write the findings to a markdown file named after the topic.

## Step 1 — Determine the topic

The research topic is: **$ARGUMENTS**

If `$ARGUMENTS` is empty, ask the user what they want researched before proceeding.

Derive a safe filename from the topic by lowercasing and replacing spaces/special characters with underscores. For example:
- "impact of LLMs on software engineering" → `impact_of_llms_on_software_engineering.md`
- "quantum computing basics" → `quantum_computing_basics.md`

## Step 2 — Launch the research analyst

Use the Agent tool with `subagent_type: "voltagent-research:research-analyst"` and provide a detailed prompt that instructs it to:

- Research the topic thoroughly using web searches and multiple credible sources
- Cover key concepts, current state, notable findings, trends, and relevant data/statistics
- Identify and cite primary sources, studies, articles, and expert opinions
- Structure findings clearly with sections: Executive Summary, Background, Key Findings, Analysis, Trends, Conclusion, References
- Return the full write-up as markdown, including a properly formatted References section with URLs

Be specific and comprehensive in your prompt — the quality of the output depends on how well the task is described.

## Step 3 — Validate the output

Before writing anything to disk, review the markdown returned by the research analyst against these checks. Fix any issues inline rather than asking the user.

**Structure checks** — the output must contain all of these sections. If any are missing, add a placeholder with a note that the section could not be completed:
- `## Executive Summary`
- `## Background`
- `## Key Findings`
- `## Analysis`
- `## Trends`
- `## Conclusion`
- `## References`

**References checks:**
- The References section must contain at least 3 entries with real URLs (not placeholder text like `[URL]` or `example.com`).
- If fewer than 3 real URLs are present, note this as a caveat in your Step 5 report — do not fabricate URLs.

**Fabricated metrics — strip these:**
- Remove any JSON progress blocks that contain fake telemetry (e.g. `"sources_analyzed": 234`, `"confidence_level": "94%"`, `"data_points": "12.4K"`). These are not real measurements.
- Remove any delivery notification boilerplate like "Analyzed 234 sources yielding 12.4K data points."

**Placeholder / incomplete content:**
- Scan for obvious placeholder text: `[INSERT]`, `[TBD]`, `[URL]`, `Lorem ipsum`, or section headings with no body content. Flag or remove these.

**Minimum length:**
- The report body (excluding the References section) must be at least 400 words. If it falls short, note this as a caveat — do not pad with filler.

## Step 4 — Write the output file

Take the validated markdown and write it to the derived filename from Step 1 in the current working directory.

If the file already exists, read it first and then decide whether to overwrite or append/merge (prefer overwriting with the new comprehensive version unless the user instructed otherwise).

## Step 5 — Report

Tell the user:
- The filename the report was written to
- A 2–3 sentence summary of what was covered
- Any validation issues found (missing sections, insufficient references, short length) and how they were handled
