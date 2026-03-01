/**
 * TypeScript type definitions for the pickleball game stats JSON format.
 * Derived from stats-2.2.0.schema.json
 */

// ---------------------------------------------------------------------------
// Primitives / shared branded types
// ---------------------------------------------------------------------------

/** A percentage value between 0 and 100. */
export type Percentage = number;

/** A quality score between 0 and 1. */
export type QualityScore = number;

/** A non-negative integer count. */
export type Count = number;

/** Speed in MPH (0–99). */
export type Speed = number;

/** Semver version string (e.g. "2.1.0"). */
export type Version = string;

// ---------------------------------------------------------------------------
// Session
// ---------------------------------------------------------------------------

export type SessionType = "game" | "drill";

export interface Session {
  session_type: SessionType;
  num_players: number;
  vid: string;
  session_index: number;
}

// ---------------------------------------------------------------------------
// Game
// ---------------------------------------------------------------------------

/** Each team's result: null (unknown), "won"/"lost", or an integer score. */
export type GameOutcomeEntry = null | "won" | "lost" | number;

export interface LongestRally {
  rally_idx: number;
  num_shots: number;
}

export interface RelativeAdjustments {
  between_teams: number;
  within_teams: [number, number];
}

export type ScoringSystem = "side_out" | "rally";
export type MinPoints = 11 | 15 | 21 | 25;

export interface GameData {
  avg_shots: number;
  game_outcome: [GameOutcomeEntry, GameOutcomeEntry];
  kitchen_rallies: number;
  longest_rally: LongestRally;
  team_percentage_to_kitchen: [Percentage, Percentage];
  scoring?: ScoringSystem;
  min_points?: MinPoints;
  relative_adjustments?: RelativeAdjustments;
}

// ---------------------------------------------------------------------------
// Shot outcome / speed stats (shared across every shot category)
// ---------------------------------------------------------------------------

export interface OutcomeStats {
  attempt_percentage: Percentage;
  success_percentage: Percentage;
  rally_won_percentage: Percentage;
  out_fault_percentage: Percentage;
  net_fault_percentage: Percentage;
  high_quality_shot_rally_won_percentage?: Percentage;
  low_quality_shot_rally_won_percentage?: Percentage;
}

export interface SpeedStats {
  fastest: Speed;
  average: Speed;
  median: Speed;
}

/**
 * Detailed stats for a shot category (serves, returns, dinks, etc.).
 * When `count` is 0 the other fields may be absent.
 */
export interface ShotCategoryStats {
  count: Count;
  outcome_stats?: OutcomeStats;
  average_quality?: QualityScore;
  average_baseline_distance?: number;
  median_baseline_distance?: number;
  average_height_above_net?: number;
  median_height_above_net?: number;
  speed_stats?: SpeedStats;
}

// ---------------------------------------------------------------------------
// Ball directions
// ---------------------------------------------------------------------------

export interface BallDirections {
  mid_cross_left_count: Count;
  mid_cross_right_count: Count;
  down_the_middle_count: Count;
  left_to_middle_count: Count;
  left_cross_right_count: Count;
  down_the_line_left_count: Count;
  right_to_middle_count: Count;
  right_cross_left_count: Count;
  down_the_line_right_count: Count;
}

// ---------------------------------------------------------------------------
// Role stats (serving / receiving × oneself / partner)
// ---------------------------------------------------------------------------

export interface RallyCategoryCounts {
  total: Count;
  kitchen_arrival: Count;
}

export interface RoleContext {
  oneself: RallyCategoryCounts;
  partner: RallyCategoryCounts;
}

export interface RoleStats {
  serving: RoleContext;
  receiving: RoleContext;
}

// ---------------------------------------------------------------------------
// Kitchen arrival percentage
// ---------------------------------------------------------------------------

export interface KitchenArrivalFraction {
  numerator: Count;
  denominator: Count;
}

export interface KitchenArrivalRoleContext {
  oneself: KitchenArrivalFraction;
  partner: KitchenArrivalFraction;
}

export interface KitchenArrivalPercentage {
  serving: KitchenArrivalRoleContext;
  returning: KitchenArrivalRoleContext;
}

// ---------------------------------------------------------------------------
// Team kitchen arrival (v2.2.0+)
// ---------------------------------------------------------------------------

export interface TeamKitchenArrival {
  serving: KitchenArrivalFraction;
  returning: KitchenArrivalFraction;
}

// ---------------------------------------------------------------------------
// Player
// ---------------------------------------------------------------------------

/** All shot-category keys present on a Player object. */
export type ShotCategoryKey =
  | "serves"
  | "returns"
  | "thirds"
  | "fourths"
  | "fifths"
  | "drives"
  | "drops"
  | "dinks"
  | "lobs"
  | "smashes"
  | "third_drives"
  | "third_drops"
  | "third_lobs"
  | "resets"
  | "speedups"
  | "passing"
  | "poaches"
  | "forehands"
  | "backhands"
  | "left_side_player"
  | "right_side_player"
  | "kitchen_area"
  | "mid_court_area"
  | "near_baseline_area"
  | "near_midline_area"
  | "near_left_sideline_area"
  | "near_right_sideline_area";

export interface Player {
  team: number;

  // Aggregate counts
  shot_count: Count;
  final_shot_count: Count;
  volley_count: Count;
  ground_stroke_count: Count;

  // Quality & impact
  average_shot_quality: QualityScore;
  net_impact_score: number;
  net_fault_percentage: Percentage;
  out_fault_percentage: Percentage;

  // Court coverage
  total_distance_covered: number;
  average_x_coverage_percentage?: Percentage;

  // Team-level metrics
  team_shot_percentage: Percentage;
  team_left_side_percentage: Percentage;
  team_short_length_rallies_won?: Percentage;
  team_medium_length_rallies_won?: Percentage;
  team_long_length_rallies_won?: Percentage;
  team_thirds_percentage: Percentage;
  team_fourths_percentage: Percentage;
  team_fifths_percentage: Percentage;

  // Structured data
  ball_directions: BallDirections;
  role_stats: RoleStats;
  kitchen_arrival_percentage: KitchenArrivalPercentage;
  team_kitchen_arrival?: TeamKitchenArrival;

  // Shot categories
  serves: ShotCategoryStats;
  returns: ShotCategoryStats;
  thirds: ShotCategoryStats;
  fourths: ShotCategoryStats;
  fifths: ShotCategoryStats;
  drives: ShotCategoryStats;
  drops: ShotCategoryStats;
  dinks: ShotCategoryStats;
  lobs: ShotCategoryStats;
  smashes: ShotCategoryStats;
  third_drives: ShotCategoryStats;
  third_drops: ShotCategoryStats;
  third_lobs: ShotCategoryStats;
  resets: ShotCategoryStats;
  speedups: ShotCategoryStats;
  passing: ShotCategoryStats;
  poaches: ShotCategoryStats;
  forehands: ShotCategoryStats;
  backhands: ShotCategoryStats;
  left_side_player: ShotCategoryStats;
  right_side_player: ShotCategoryStats;
  kitchen_area: ShotCategoryStats;
  mid_court_area: ShotCategoryStats;
  near_baseline_area: ShotCategoryStats;
  near_midline_area: ShotCategoryStats;
  near_left_sideline_area: ShotCategoryStats;
  near_right_sideline_area: ShotCategoryStats;
}

// ---------------------------------------------------------------------------
// Top-level document
// ---------------------------------------------------------------------------

export interface StatsDocument {
  version: Version;
  session: Session;
  game: GameData;
  players: Array<Player | null>;
}
