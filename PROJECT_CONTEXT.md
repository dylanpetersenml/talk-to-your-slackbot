# PB Coach Knowledge Agent — Project Context

Pickleball match review Slackbot that analyzes PB Vision match statistics (`stats.json`) from recorded games and returns coaching insights. Users ask questions in Slack (e.g. *"How did I lose this game?"*); the agent analyzes match stats and responds with insights based on shot patterns, errors, and decision making. The concise insight summary is provied in the slack channel.

The agent reduces manual review time for data analysis of the pickleball match providing higher-level insights.

# System Scope
# In Scope
- parsing and validating structured inputs from slack
- planning investigation from the provided match statistics
- Reasoning about key data points provided
- Formatting and delivering analysis summary to slack
- Guardrails for input validation and output safety and accuracy

For coding conventions and agent instructions, see **AGENTS.md**.

# Out of Scope
- Direct integration with pbvision access to other matches
- Historical anomaly patterns: assuming single match data
- Computer Vision analysis on pickleball mechanics


---

## Tech stack

- **Runtime:** Python; Slack API for messages.
- **Analysis:** PandasAI over structured stats; semantic layer in `pickleball_stats.yaml`.
- **Schema:** `stats.json` follows `stats-2.2.0.schema.json` (PB Vision 2.x).
- **Secrets:** Use environment variables only; see `.env.example`. Never commit secrets.

---

## Project layout

| Path | Purpose |
|------|--------|
| `talk-to-your-slackbot/` | Main package and entrypoint (`main.py`) |
| `stats.json` | Sample/match stats (PB Vision); production data from S3 |
| `pickleball_stats.yaml` | Semantic model for PandasAI (entities, measures, dimensions) |
| `stats-2.2.0.schema.json` | JSON schema for `stats.json` |
| `.env.example` | Required env vars (no real values) |



---

## Data

- **Source:** `stats.json` from PB Vision (S3). Loaded by the agent per request.
- **Structure:** Top-level `session`, `game`, `players` (per-player `ball_directions`, `role_stats`, `kitchen_arrival_percentage`, etc.), and rally-level data. Use `pickleball_stats.yaml` for queryable entities and measures.
- **Optional:** Extra metrics or data-cleaning (e.g. abnormal mph on drives) can be added later.

---

## Pipeline / Architecture Summary

**Input** → **Intake** → **Engine** → **Output**

### 1. Input

- User question from Slack (e.g. *"How did I lose this game?"*, *"Where did we give up the most points?"*, *"Compare my serving vs returning"*).

### 2. Intake subsystem

- **Input parser:** Prompt length validation; format check (valid text).
- **Guardrails:** PII detection; permission check (user has access to the data; question is applicable to the data source).

The intake subsystem ensures that only properly formatted and validated text input proceed to the engine.

### 3. Engine
The engine performs the core investigation loci through two components:


- Load `stats.json` (pickleball stats).
- **Planner:**: Determines which fields to investigate. Interacts with Memory to leverage past investigation patterns if have multiple matches. In other words, decides how to answer the question and which stats to use.
- **Reasoner (PandasAI):** Analyze key factors (e.g. return depth distribution, kitchen arrival, shot directions) using the semantic layer of picklenall_stats.yaml


- **Insight generator:** Turn analysis into a clear coaching sentence (e.g. *"Your short returns were a key driver for losing the game"*).

### 4. Output Subsystem
Output subsystem for the final analysis.
- **output Formatter:** Structures the analysis results into a concise suitable for slack delivery. Incorporates both the engine and prior Memory for contextual insights 

- **Output Guarrails:** Ensures accuracy of the formatted output before delivery

---

## Design principles

- Insights should reflect **shot quality**, **decision making**, **errors**, and **shot patterns**.
- Reasoning is driven by PandasAI over the structured stats; guardrails and parser protect safety and relevance before the engine runs.

---

## Edge cases and errors

- **Missing or malformed `stats.json`:** Return a clear, user-friendly message; do not expose stack traces.
- **Wrong session or no matching data:** Confirm the question applies to the loaded game (e.g. correct `vid`/session); respond accordingly if not.
- **Empty or partial stats:** Handle gracefully; avoid assumptions that required fields exist without checks.
