/**
 * The contract's own bit flags, decoded in the browser.
 *
 * `HelmTypes.sol` packs every rule the enforcer applied into one byte, and `HelmReject`
 * packs the reason a proposal was thrown away into one byte. Both are bit *flags*, not a
 * sequence, so the positions matter:
 *
 *   bit 0  LP_ABOVE_MAX       bit 3  RANGE_BELOW_MIN
 *   bit 1  LP_BELOW_MIN       bit 4  VOLATILITY_EXIT
 *   bit 2  RANGE_ABOVE_MAX    bit 5  ECONOMIC_VETO
 *                             bit 6  NO_TRADE
 *
 * The dashboard shows the names the chain published, not the agent's guess, so a judge
 * reading the page sees the same thing the transaction says.
 */

export const CLAMP_BITS: Array<[number, string]> = [
  [1 << 0, "LP_ABOVE_MAX"],
  [1 << 1, "LP_BELOW_MIN"],
  [1 << 2, "RANGE_ABOVE_MAX"],
  [1 << 3, "RANGE_BELOW_MIN"],
  [1 << 4, "VOLATILITY_EXIT"],
  [1 << 5, "ECONOMIC_VETO"],
  [1 << 6, "NO_TRADE"],
];

export const REJECT_BITS: Array<[number, string]> = [
  [1 << 0, "UNKNOWN_AGENT"],
  [1 << 1, "CYCLE_MISMATCH"],
  [1 << 2, "STALE"],
  [1 << 3, "NO_LIMITS"],
  [1 << 4, "PAUSED"],
  [1 << 5, "REPLAY"],
  [1 << 6, "BAD_INPUT"],
];

/** The names of every clamp bit set in `mask`. */
export function clampNames(mask: number | null | undefined): string[] {
  if (!mask) return [];
  return CLAMP_BITS.filter(([bit]) => (mask & bit) !== 0).map(([, name]) => name);
}

/** The names of every reject flag set in `reason`. */
export function rejectNames(reason: number | null | undefined): string[] {
  if (!reason) return [];
  const known = REJECT_BITS.filter(([bit]) => (reason & bit) !== 0).map(([, name]) => name);
  const unknownBits = reason & ~REJECT_BITS.reduce((acc, [bit]) => acc | bit, 0);
  if (unknownBits) known.push(`UNKNOWN_${unknownBits}`);
  return known;
}
