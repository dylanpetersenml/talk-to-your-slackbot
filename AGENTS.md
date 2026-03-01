# AGENTS.md

## Cursor Cloud specific instructions

### Overview
TypeScript project providing typed interfaces and Zod runtime validation for pickleball game stats JSON (v2.1.0 / v2.2.0 format). No backend services or databases.

### Commands
See `package.json` scripts. Key commands:
- `npm run lint` — type-check via `tsc --noEmit`
- `npm test` — vitest suite (23 tests)
- `npm run build` — compile to `dist/`
- `npm run validate` — validate `data/stats.json` against Zod schema

### Gotchas
- Zod v4 uses `import { z } from "zod/v4"` (not `from "zod"`).
- The `tsconfig.json` `include` is scoped to `src/`; tests live in `tests/` and are run by vitest (which has its own TS handling via `vitest.config.ts`).
- The sample `data/stats.json` is v2.1.0 and lacks `team_kitchen_arrival` (added in v2.2.0); the schema marks that field optional.
