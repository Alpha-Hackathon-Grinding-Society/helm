/**
 * The split bar: the model's number, the contract's envelope, and what actually
 * happened, in one strip.
 *
 * The track runs from 0% LP (far left) to 100% LP (far right). The blue region is the
 * liquidity position the contract actually took, the green region is lending, the amber
 * band is the part of the model's proposal the contract removed, the amber line is the
 * model's raw number and the white line is the number that was enforced.
 *
 * A clamped cycle is therefore visible before a single word is read: there is an amber
 * band where the model and the contract disagree.
 */
export type SplitBarProps = {
  modelLpShareBps: number;
  finalLpShareBps: number;
  minBps?: number;
  maxBps?: number;
  showTicks?: boolean;
  label?: string;
};

const clamp = (value: number, low = 0, high = 10000) =>
  Math.min(high, Math.max(low, value));

export function SplitBar({
  modelLpShareBps,
  finalLpShareBps,
  minBps,
  maxBps,
  showTicks = false,
  label,
}: SplitBarProps) {
  const model = clamp(modelLpShareBps);
  const final = clamp(finalLpShareBps);
  const clamped = Math.abs(model - final) >= 1;
  const bandLeft = Math.min(model, final) / 100;
  const bandWidth = Math.abs(model - final) / 100;

  const description = clamped
    ? `The model proposed ${(model / 100).toFixed(2)}% liquidity; the contract enforced ${(
        final / 100
      ).toFixed(2)}%.`
    : `The contract enforced ${(final / 100).toFixed(2)}% liquidity, which matches the model's proposal.`;

  return (
    <div>
      <div
        className="split"
        role="img"
        aria-label={label ? `${label}. ${description}` : description}
      >
        <div className="split-lp" style={{ width: `${final / 100}%` }} />
        <div className="split-lending" style={{ width: `${(10000 - final) / 100}%` }} />
        {clamped ? (
          <div
            className="split-clamp"
            style={{ left: `${bandLeft}%`, width: `${bandWidth}%` }}
          />
        ) : null}
        <div className="split-proposed" style={{ left: `${model / 100}%` }} />
        <div className="split-final" style={{ left: `${final / 100}%` }} />
        {showTicks && minBps !== undefined && maxBps !== undefined ? (
          <>
            <div className="split-tick" style={{ left: `${minBps / 100}%` }} />
            <div className="split-tick" style={{ left: `${maxBps / 100}%` }} />
          </>
        ) : null}
      </div>
      <div className="split-legend">
        <span className="legend-key">
          <span className="legend-swatch" style={{ background: "var(--lp-dim)", border: "1px solid var(--lp)" }} />
          LP {((final) / 100).toFixed(2)}%
        </span>
        <span className="legend-key">
          <span className="legend-swatch" style={{ background: "var(--lending-dim)", border: "1px solid var(--lending)" }} />
          Lending {((10000 - final) / 100).toFixed(2)}%
        </span>
        <span className="legend-key">
          <span className="legend-swatch" style={{ background: "var(--clamp)" }} />
          Model {(model / 100).toFixed(2)}%
        </span>
        {clamped ? (
          <span className="legend-key" style={{ color: "var(--clamp)" }}>
            clamped by contract
          </span>
        ) : null}
      </div>
    </div>
  );
}
