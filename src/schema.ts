/**
 * Zod validation schemas for the pickleball game stats JSON format.
 * Derived from stats-2.2.0.schema.json – works for v2.1.0 and v2.2.0 data.
 */
import { z } from "zod/v4";

// ---------------------------------------------------------------------------
// Primitives
// ---------------------------------------------------------------------------

export const PercentageSchema = z.number().min(0).max(100);
export const QualityScoreSchema = z.number().min(0).max(1);
export const CountSchema = z.int().min(0);
export const SpeedSchema = z.number().min(0).max(99);
export const VersionSchema = z.string().regex(/^\d+\.\d+\.\d+(-[^\s]+)?$/);

// ---------------------------------------------------------------------------
// Session
// ---------------------------------------------------------------------------

export const SessionTypeSchema = z.enum(["game", "drill"]);

export const SessionSchema = z
  .object({
    session_type: SessionTypeSchema,
    num_players: z.int().min(1).max(4),
    vid: z.string(),
    session_index: z.int(),
  })
  .strict();

// ---------------------------------------------------------------------------
// Game
// ---------------------------------------------------------------------------

export const GameOutcomeEntrySchema = z.union([
  z.null(),
  z.enum(["won", "lost"]),
  z.int().min(0),
]);

export const LongestRallySchema = z
  .object({
    rally_idx: z.int().min(0),
    num_shots: z.int().min(0),
  })
  .strict();

export const RelativeAdjustmentsSchema = z
  .object({
    between_teams: z.number(),
    within_teams: z.tuple([z.number(), z.number()]),
  })
  .strict();

export const ScoringSystemSchema = z.enum(["side_out", "rally"]);
export const MinPointsSchema = z.union([
  z.literal(11),
  z.literal(15),
  z.literal(21),
  z.literal(25),
]);

export const GameDataSchema = z
  .object({
    avg_shots: z.number().min(1),
    game_outcome: z.tuple([GameOutcomeEntrySchema, GameOutcomeEntrySchema]),
    kitchen_rallies: z.int().min(0),
    longest_rally: LongestRallySchema,
    team_percentage_to_kitchen: z.tuple([
      PercentageSchema,
      PercentageSchema,
    ]),
    scoring: ScoringSystemSchema.optional(),
    min_points: MinPointsSchema.optional(),
    relative_adjustments: RelativeAdjustmentsSchema.optional(),
  })
  .strict();

// ---------------------------------------------------------------------------
// Shot outcome / speed stats
// ---------------------------------------------------------------------------

export const OutcomeStatsSchema = z
  .object({
    attempt_percentage: PercentageSchema,
    success_percentage: PercentageSchema,
    rally_won_percentage: PercentageSchema,
    out_fault_percentage: PercentageSchema,
    net_fault_percentage: PercentageSchema,
    high_quality_shot_rally_won_percentage: PercentageSchema.optional(),
    low_quality_shot_rally_won_percentage: PercentageSchema.optional(),
  })
  .strict();

export const SpeedStatsSchema = z
  .object({
    fastest: SpeedSchema,
    average: SpeedSchema,
    median: SpeedSchema,
  })
  .strict();

export const ShotCategoryStatsSchema = z
  .object({
    count: CountSchema,
    outcome_stats: OutcomeStatsSchema.optional(),
    average_quality: QualityScoreSchema.optional(),
    average_baseline_distance: z.number().optional(),
    median_baseline_distance: z.number().optional(),
    average_height_above_net: z.number().optional(),
    median_height_above_net: z.number().optional(),
    speed_stats: SpeedStatsSchema.optional(),
  })
  .strict();

// ---------------------------------------------------------------------------
// Ball directions
// ---------------------------------------------------------------------------

export const BallDirectionsSchema = z
  .object({
    mid_cross_left_count: CountSchema,
    mid_cross_right_count: CountSchema,
    down_the_middle_count: CountSchema,
    left_to_middle_count: CountSchema,
    left_cross_right_count: CountSchema,
    down_the_line_left_count: CountSchema,
    right_to_middle_count: CountSchema,
    right_cross_left_count: CountSchema,
    down_the_line_right_count: CountSchema,
  })
  .strict();

// ---------------------------------------------------------------------------
// Role stats
// ---------------------------------------------------------------------------

export const RallyCategoryCountsSchema = z
  .object({
    total: CountSchema,
    kitchen_arrival: CountSchema,
  })
  .strict();

export const RoleContextSchema = z
  .object({
    oneself: RallyCategoryCountsSchema,
    partner: RallyCategoryCountsSchema,
  })
  .strict();

export const RoleStatsSchema = z
  .object({
    serving: RoleContextSchema,
    receiving: RoleContextSchema,
  })
  .strict();

// ---------------------------------------------------------------------------
// Kitchen arrival percentage
// ---------------------------------------------------------------------------

export const KitchenArrivalFractionSchema = z
  .object({
    numerator: CountSchema,
    denominator: CountSchema,
  })
  .strict();

export const KitchenArrivalRoleContextSchema = z
  .object({
    oneself: KitchenArrivalFractionSchema,
    partner: KitchenArrivalFractionSchema,
  })
  .strict();

export const KitchenArrivalPercentageSchema = z
  .object({
    serving: KitchenArrivalRoleContextSchema,
    returning: KitchenArrivalRoleContextSchema,
  })
  .strict();

// ---------------------------------------------------------------------------
// Team kitchen arrival (v2.2.0+)
// ---------------------------------------------------------------------------

export const TeamKitchenArrivalSchema = z
  .object({
    serving: KitchenArrivalFractionSchema,
    returning: KitchenArrivalFractionSchema,
  })
  .strict();

// ---------------------------------------------------------------------------
// Player
// ---------------------------------------------------------------------------

export const PlayerSchema = z
  .object({
    team: z.int(),

    // Aggregate counts
    shot_count: CountSchema,
    final_shot_count: CountSchema,
    volley_count: CountSchema,
    ground_stroke_count: CountSchema,

    // Quality & impact
    average_shot_quality: QualityScoreSchema,
    net_impact_score: z.number(),
    net_fault_percentage: PercentageSchema,
    out_fault_percentage: PercentageSchema,

    // Court coverage
    total_distance_covered: z.number(),
    average_x_coverage_percentage: PercentageSchema.optional(),

    // Team-level metrics
    team_shot_percentage: PercentageSchema,
    team_left_side_percentage: PercentageSchema,
    team_short_length_rallies_won: PercentageSchema.optional(),
    team_medium_length_rallies_won: PercentageSchema.optional(),
    team_long_length_rallies_won: PercentageSchema.optional(),
    team_thirds_percentage: PercentageSchema,
    team_fourths_percentage: PercentageSchema,
    team_fifths_percentage: PercentageSchema,

    // Structured data
    ball_directions: BallDirectionsSchema,
    role_stats: RoleStatsSchema,
    kitchen_arrival_percentage: KitchenArrivalPercentageSchema,
    team_kitchen_arrival: TeamKitchenArrivalSchema.optional(),

    // Shot categories
    serves: ShotCategoryStatsSchema,
    returns: ShotCategoryStatsSchema,
    thirds: ShotCategoryStatsSchema,
    fourths: ShotCategoryStatsSchema,
    fifths: ShotCategoryStatsSchema,
    drives: ShotCategoryStatsSchema,
    drops: ShotCategoryStatsSchema,
    dinks: ShotCategoryStatsSchema,
    lobs: ShotCategoryStatsSchema,
    smashes: ShotCategoryStatsSchema,
    third_drives: ShotCategoryStatsSchema,
    third_drops: ShotCategoryStatsSchema,
    third_lobs: ShotCategoryStatsSchema,
    resets: ShotCategoryStatsSchema,
    speedups: ShotCategoryStatsSchema,
    passing: ShotCategoryStatsSchema,
    poaches: ShotCategoryStatsSchema,
    forehands: ShotCategoryStatsSchema,
    backhands: ShotCategoryStatsSchema,
    left_side_player: ShotCategoryStatsSchema,
    right_side_player: ShotCategoryStatsSchema,
    kitchen_area: ShotCategoryStatsSchema,
    mid_court_area: ShotCategoryStatsSchema,
    near_baseline_area: ShotCategoryStatsSchema,
    near_midline_area: ShotCategoryStatsSchema,
    near_left_sideline_area: ShotCategoryStatsSchema,
    near_right_sideline_area: ShotCategoryStatsSchema,
  })
  .strict();

// ---------------------------------------------------------------------------
// Top-level document
// ---------------------------------------------------------------------------

export const StatsDocumentSchema = z
  .object({
    version: VersionSchema,
    session: SessionSchema,
    game: GameDataSchema,
    players: z.array(PlayerSchema.nullable()),
  })
  .strict();

// ---------------------------------------------------------------------------
// Inferred types (kept in sync with the Zod schemas automatically)
// ---------------------------------------------------------------------------

export type StatsDocumentInferred = z.infer<typeof StatsDocumentSchema>;
export type PlayerInferred = z.infer<typeof PlayerSchema>;
export type GameDataInferred = z.infer<typeof GameDataSchema>;
export type SessionInferred = z.infer<typeof SessionSchema>;
