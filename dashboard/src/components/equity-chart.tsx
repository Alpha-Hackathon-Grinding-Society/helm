/**
 * A hand-drawn equity chart.
 *
 * The backtest has five equity curves and they cross each other constantly, so the
 * chart is deliberately plain: one line per strategy, one y-axis in dollars, one x-axis
 * in bars. No smoothing and no second axis, because both would make the curves look
 * better than the backtest is.
 */
export type Series = {
  key: string;
  label: string;
  color: string;
  points: number[];
};

export function EquityChart({ series, height = 300 }: { series: Series[]; height?: number }) {
  const width = 960;
  const pad = { top: 14, right: 14, bottom: 26, left: 62 };
  const usableWidth = width - pad.left - pad.right;
  const usableHeight = height - pad.top - pad.bottom;

  const all = series.flatMap((s) => s.points).filter((v) => Number.isFinite(v));
  if (all.length === 0) {
    return <div className="state">No equity points to plot yet.</div>;
  }

  const rawMin = Math.min(...all);
  const rawMax = Math.max(...all);
  const span = rawMax - rawMin || Math.max(1, Math.abs(rawMax));
  const min = rawMin - span * 0.08;
  const max = rawMax + span * 0.08;

  const length = Math.max(...series.map((s) => s.points.length));
  const x = (index: number) => pad.left + (usableWidth * index) / Math.max(1, length - 1);
  const y = (value: number) => pad.top + usableHeight * ((max - value) / (max - min));

  const ticks = [max, max - (max - min) / 2, min];

  return (
    <div>
      <svg
        className="chart"
        viewBox={`0 0 ${width} ${height}`}
        preserveAspectRatio="xMidYMid meet"
        role="img"
        aria-label="Equity curves for each strategy over the backtest window"
      >
        {ticks.map((tick, i) => (
          <g key={i}>
            <line
              className="chart-grid"
              x1={pad.left}
              x2={width - pad.right}
              y1={y(tick)}
              y2={y(tick)}
            />
            <text className="chart-label" x={pad.left - 8} y={y(tick) + 3} textAnchor="end">
              {formatMoney(tick)}
            </text>
          </g>
        ))}
        <line
          className="chart-axis"
          x1={pad.left}
          x2={width - pad.right}
          y1={pad.top + usableHeight}
          y2={pad.top + usableHeight}
        />
        <text
          className="chart-label"
          x={pad.left}
          y={height - 8}
          textAnchor="start"
        >
          bar 0
        </text>
        <text
          className="chart-label"
          x={width - pad.right}
          y={height - 8}
          textAnchor="end"
        >
          bar {length - 1}
        </text>
        {series.map((s) => {
          if (s.points.length === 0) return null;
          const path = s.points
            .map((value, index) => `${index === 0 ? "M" : "L"}${x(index).toFixed(2)},${y(value).toFixed(2)}`)
            .join(" ");
          return (
            <path
              key={s.key}
              className="chart-line"
              d={path}
              stroke={s.color}
              strokeWidth={s.key === "model" ? 2.25 : 1.5}
            />
          );
        })}
      </svg>
      <div className="split-legend">
        {series.map((s) => (
          <span className="legend-key" key={s.key}>
            <span className="legend-swatch" style={{ background: s.color }} />
            {s.label}
          </span>
        ))}
      </div>
    </div>
  );
}

function formatMoney(value: number): string {
  if (Math.abs(value) >= 1000) {
    return `$${(value / 1000).toFixed(1)}k`;
  }
  return `$${value.toFixed(0)}`;
}
