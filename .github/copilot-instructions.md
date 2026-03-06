# GitHub Copilot Instructions for `talk-to-your-slackbot`

A Python Slack bot that synthesizes Pickleball Vision stats data into coaching insights. The project integrates tournament match analytics (stats.json, schema v2.2.0) with a semantic model (pickleball_stats.yaml) to deliver actionable performance feedback via Slack.

---

## 📦 Project layout & conventions

1. **Package name**: `talk-to-your-slackbot` (importable as `talk_to_your_slackbot`). All application code lives under `talk-to-your-slackbot/`.
2. **Data & schemas**: 
   - `stats.json` — raw match data from Pickleball Vision (2458 lines, includes player stats, rally details, shot metrics).
   - `pickleball_stats.yaml` — semantic model for the stats schema (entities: game, player, rally; aligned to schema v2.2.0).
   - `stats-2.2.0.schema.json` — formal schema definition for validation.
3. `pyproject.toml` is the single source of truth for dependencies. Currently empty; add libraries with `pip install -e .`.
4. No tests yet. If added, use `tests/` directory and `pytest` convention.
5. Standard Python naming: snake_case for functions/files, PascalCase for classes.
6. `main.py` is the entry point; `__init__.py` is empty (add `__all__` when exposing public API).

---

## ⚙️ Expected workflows

* **Adding/locking dependencies**: modify `pyproject.toml` and run
  `pip install -e .` (or `poetry install` if that workflow is chosen).
* **Running the bot**: `python -m talk_to_your_slackbot.main` or
  `python -m talk_to_your_slackbot` once an entry point is defined.
* **Formatting/linting**: none enforced yet, but feel free to add `black`
  / `flake8` etc. and update the instructions accordingly.
* **Testing**: no test command exists; once tests are added, run `pytest` from
  the workspace root.

> **Note:** There is currently no CI configuration or GitHub Actions.  Do not
> assume any automated checks are running.

---

## 🔌 Slack integration points

* The whole purpose of the project is to talk to Slack.  Use the official
  [`slack_sdk`](https://pypi.org/project/slack-sdk/) and either the
  [`SoCore workflows

* **Dependencies**: Edit `pyproject.toml`, then `pip install -e .`. Likely dependencies: `slack-sdk`, `pyyaml` (for semantic model), `pandas`/`polars` (for stats analysis).
* **Run bot**: `python -m talk_to_your_slackbot.main` (entry point not yet defined).
* **Stats analysis**: Load and parse `stats.json` against schema. Use `pickleball_stats.yaml` as a guide for interpreting player stats, rally data, and shot metrics.
* **No CI/tests/linting enforced** — add these as needed and update instructions
def main():
    client = SocketModeClient(token=os.environ["SLACK_APP_TOKEN"])
    # register handlers
    client.start()
```

---

## 🛠️ Project-specific patterns

* Since exis& analytics architecture

**Slack integration**: Use `slack_sdk.socket_mode.SocketModeClient` for real-time event handling. Credentials via `SLACK_BOT_TOKEN` and `SLACK_APP_TOKEN` (stored in `.env`).

**Analytics pipeline**:
1. **Ingest**: Load `stats.json` (raw match data) and validate against `stats-2.2.0.schema.json`.
2. **Semantic layer**: Map raw data to entities defined in `pickleball_stats.yaml` (game, player, rally) for structured querying.
3. **Insights**: Extract coaching-relevant metrics (shot quality, decision-making, consistency, error rates) — see `prompt.md` for analysis examples.
4. **Delivery**: Format insights as Slack messages targeted to relevant player(s).

**Key data flows**:
- `stats.json` → validation → semantic model → analysis → Slack message
- Each player has role-specific stats (serving, returning, volley/ground stroke counts, kitchen arrival %, shot quality).
- Reference `prompt.md` for context on expected coaching insights (focus on shot quality, decision-making, error analysis).