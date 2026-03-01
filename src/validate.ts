/**
 * CLI helper: validate a stats JSON file against the Zod schema.
 * Usage: npx tsx src/validate.ts [path-to-stats.json]
 */
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { StatsDocumentSchema } from "./schema.js";

const filePath = resolve(process.argv[2] ?? "data/stats.json");
const raw = JSON.parse(readFileSync(filePath, "utf-8"));
const result = StatsDocumentSchema.safeParse(raw);

if (result.success) {
  const doc = result.data;
  console.log(`✅  Valid stats document (v${doc.version})`);
  console.log(`    Session: ${doc.session.session_type} — ${doc.session.num_players} players`);
  console.log(`    Game outcome: ${JSON.stringify(doc.game.game_outcome)}`);
  console.log(`    Players: ${doc.players.filter(Boolean).length} tracked`);
  process.exit(0);
} else {
  console.error("❌  Validation failed:\n");
  console.error(JSON.stringify(result.error.issues, null, 2));
  process.exit(1);
}
