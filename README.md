# talk-to-your-slackbot

Schema layer for pickleball game stats (`stats.json`).

## Quick start

```bash
npm install
npm run build     # compile TypeScript → dist/
npm run lint      # type-check without emitting
npm run test      # run vitest suite
npm run validate  # validate data/stats.json against the Zod schema
```

## Project structure

```
src/
  types.ts    – TypeScript interfaces for every stats object
  schema.ts   – Zod validation schemas (runtime-safe parsing)
  validate.ts – CLI helper to validate a stats JSON file
  index.ts    – barrel re-export
data/
  stats.json              – sample v2.1.0 game data
  stats-2.2.0.schema.json – upstream JSON Schema (reference)
tests/
  schema.test.ts – vitest suite (23 tests)
```
