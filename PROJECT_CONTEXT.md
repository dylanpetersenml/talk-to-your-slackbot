# PB Coach Knowledge Agent — Project Context

Pickleball match review Slackbot that analyzes PB Vision match statistics (`stats.json`) from recorded games and returns coaching insights. Users ask questions in Slack (e.g. *"How did I lose this game?"*); the agent analyzes match stats and responds with insights based on shot patterns, errors, and decision making.

---

## Data

- **Source:** `stats.json` from PB Vision (S3). Loaded by the agent for each request.
- **Optional:** One or two extra metrics or data-cleaning steps (e.g. abnormal mph on drives for speed metrics).

---

## Pipeline

**Input** → **Intake** → **Engine** → **Output**

### 1. Input

- User question from Slack (e.g. *"How did I lose this game?"*).

### 2. Intake

- **Input parser:** Prompt length validation; format check (e.g. is the input valid text?).
- **Guardrails:** PII detection; permission check (user has access to the data and question is applicable to the data source).

### 3. Engine

- Load `stats.json` (pickleball stats).
- **Reasoner (PandasAI):** Analyze key factors (e.g. `check_return_depth_distribution()` and similar metrics).
- **Planner:** Decide how to answer the question and which stats to use.
- **Insight generator:** Turn analysis into a clear coaching sentence (e.g. *"Your short returns were a key driver for losing the game"*).

### 4. Output

- Text insight returned to the user in Slack.

---

## Design principles

- Insights should reflect **shot quality**, **decision making**, **errors**, and **shot patterns**.
- Reasoning is driven by PandasAI over the structured stats; guardrails and parser protect safety and relevance before the engine runs.
