import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import {
  StatsDocumentSchema,
  SessionSchema,
  GameDataSchema,
  PlayerSchema,
  ShotCategoryStatsSchema,
  BallDirectionsSchema,
  OutcomeStatsSchema,
  SpeedStatsSchema,
  RoleStatsSchema,
  KitchenArrivalPercentageSchema,
} from "../src/schema.js";
import type { StatsDocument } from "../src/types.js";

const samplePath = resolve(import.meta.dirname, "../data/stats.json");
const sampleData = JSON.parse(readFileSync(samplePath, "utf-8"));

// ---------------------------------------------------------------------------
// Full document validation
// ---------------------------------------------------------------------------

describe("StatsDocumentSchema", () => {
  it("validates the sample stats.json", () => {
    const result = StatsDocumentSchema.safeParse(sampleData);
    expect(result.success).toBe(true);
  });

  it("rejects a document missing required fields", () => {
    const result = StatsDocumentSchema.safeParse({ version: "2.1.0" });
    expect(result.success).toBe(false);
  });

  it("rejects unknown top-level properties", () => {
    const result = StatsDocumentSchema.safeParse({
      ...sampleData,
      extra: true,
    });
    expect(result.success).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// Session
// ---------------------------------------------------------------------------

describe("SessionSchema", () => {
  it("accepts a valid game session", () => {
    const result = SessionSchema.safeParse({
      session_type: "game",
      num_players: 4,
      vid: "abc123",
      session_index: 0,
    });
    expect(result.success).toBe(true);
  });

  it("accepts a drill session", () => {
    const result = SessionSchema.safeParse({
      session_type: "drill",
      num_players: 1,
      vid: "xyz",
      session_index: 2,
    });
    expect(result.success).toBe(true);
  });

  it("rejects invalid session_type", () => {
    const result = SessionSchema.safeParse({
      session_type: "practice",
      num_players: 2,
      vid: "v",
      session_index: 0,
    });
    expect(result.success).toBe(false);
  });

  it("rejects num_players > 4", () => {
    const result = SessionSchema.safeParse({
      session_type: "game",
      num_players: 5,
      vid: "v",
      session_index: 0,
    });
    expect(result.success).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// Game data
// ---------------------------------------------------------------------------

describe("GameDataSchema", () => {
  it("validates sample game data", () => {
    const result = GameDataSchema.safeParse(sampleData.game);
    expect(result.success).toBe(true);
  });

  it("accepts game_outcome with nulls", () => {
    const result = GameDataSchema.safeParse({
      ...sampleData.game,
      game_outcome: [null, null],
    });
    expect(result.success).toBe(true);
  });

  it("accepts game_outcome with won/lost strings", () => {
    const result = GameDataSchema.safeParse({
      ...sampleData.game,
      game_outcome: ["won", "lost"],
    });
    expect(result.success).toBe(true);
  });

  it("rejects avg_shots < 1", () => {
    const result = GameDataSchema.safeParse({
      ...sampleData.game,
      avg_shots: 0,
    });
    expect(result.success).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// Player
// ---------------------------------------------------------------------------

describe("PlayerSchema", () => {
  it("validates each player in sample data", () => {
    for (const player of sampleData.players) {
      if (player === null) continue;
      const result = PlayerSchema.safeParse(player);
      if (!result.success) {
        console.error(
          `Player team=${player.team} failed:`,
          JSON.stringify(result.error.issues, null, 2)
        );
      }
      expect(result.success).toBe(true);
    }
  });

  it("allows null in the players array", () => {
    const result = StatsDocumentSchema.safeParse({
      ...sampleData,
      players: [null, null, null, null],
    });
    expect(result.success).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// Shot category stats
// ---------------------------------------------------------------------------

describe("ShotCategoryStatsSchema", () => {
  it("accepts a category with count 0 and no other fields", () => {
    const result = ShotCategoryStatsSchema.safeParse({ count: 0 });
    expect(result.success).toBe(true);
  });

  it("accepts a fully populated shot category", () => {
    const result = ShotCategoryStatsSchema.safeParse(
      sampleData.players[0].serves
    );
    expect(result.success).toBe(true);
  });

  it("rejects negative count", () => {
    const result = ShotCategoryStatsSchema.safeParse({ count: -1 });
    expect(result.success).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// Outcome stats
// ---------------------------------------------------------------------------

describe("OutcomeStatsSchema", () => {
  it("validates sample outcome stats", () => {
    const result = OutcomeStatsSchema.safeParse(
      sampleData.players[0].serves.outcome_stats
    );
    expect(result.success).toBe(true);
  });

  it("rejects percentage > 100", () => {
    const result = OutcomeStatsSchema.safeParse({
      attempt_percentage: 101,
      success_percentage: 50,
      rally_won_percentage: 50,
      out_fault_percentage: 0,
      net_fault_percentage: 0,
    });
    expect(result.success).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// Speed stats
// ---------------------------------------------------------------------------

describe("SpeedStatsSchema", () => {
  it("validates sample speed stats", () => {
    const result = SpeedStatsSchema.safeParse(
      sampleData.players[0].serves.speed_stats
    );
    expect(result.success).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// Ball directions
// ---------------------------------------------------------------------------

describe("BallDirectionsSchema", () => {
  it("validates sample ball directions", () => {
    const result = BallDirectionsSchema.safeParse(
      sampleData.players[0].ball_directions
    );
    expect(result.success).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// Role stats & kitchen arrival
// ---------------------------------------------------------------------------

describe("RoleStatsSchema", () => {
  it("validates sample role stats", () => {
    const result = RoleStatsSchema.safeParse(
      sampleData.players[0].role_stats
    );
    expect(result.success).toBe(true);
  });
});

describe("KitchenArrivalPercentageSchema", () => {
  it("validates sample kitchen arrival data", () => {
    const result = KitchenArrivalPercentageSchema.safeParse(
      sampleData.players[0].kitchen_arrival_percentage
    );
    expect(result.success).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// Type compatibility check (compile-time)
// ---------------------------------------------------------------------------

describe("type compatibility", () => {
  it("parsed data satisfies StatsDocument interface", () => {
    const result = StatsDocumentSchema.safeParse(sampleData);
    expect(result.success).toBe(true);
    if (result.success) {
      const doc: StatsDocument = result.data;
      expect(doc.version).toBe("2.1.0");
      expect(doc.players).toHaveLength(4);
    }
  });
});
