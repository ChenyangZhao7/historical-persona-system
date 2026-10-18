// Canonical dimension keys, in the order used by services/matcher.py
// (DIMENSIONS) and by the short labels in each page's DIMS array.
export const DIMENSION_LABELS = {
  reaction_to_oppression: "Oppression",
  group_dependency: "Group",
  principle_vs_interest: "Principle",
  interpersonal_trust: "Trust",
  change_orientation: "Change",
  emotional_stability: "Emotion",
  core_motivation: "Motivation",
  historical_mission: "Mission",
  response_to_injustice: "Injustice",
  expression_style: "Expression",
}

export function dimensionLabel(key) {
  return DIMENSION_LABELS[key] || key
}

// Canonical order, for code that compares raw vectors positionally.
export const DIMENSION_KEYS = Object.keys(DIMENSION_LABELS)
