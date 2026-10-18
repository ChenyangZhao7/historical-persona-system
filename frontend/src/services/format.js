// Shared formatting for figure era values.
//
// `era` is a birth year: negative = BC, NULL = not dated. Every page used to
// inline `era < 0 ? ... : \`${era} AD\``, which printed "null AD" for the four
// figures whose birth date is unknown. Keep the rules in one place.

export function formatEra(era) {
  if (era === null || era === undefined || Number.isNaN(era) || era === 0) {
    return "era unknown"
  }
  return era < 0 ? `${Math.abs(era)} BC` : `${era} AD`
}
