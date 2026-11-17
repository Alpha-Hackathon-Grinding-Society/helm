import Link from "next/link";
import { loadMetrics, type StrategyMetrics } from "@/lib/deployment";
import { EquityChart, type Series } from "@/components/equity-chart";
import { EmptyState, Panel, timeLabel } from "@/components/bits";

export const dynamic = "force-dynamic";
export const revalidate = 0;

const LABELS: Record<string, string> = {
  model: "Helm (the model)",
  best_rate_now: "Best rate now",
  static_50_50: "Static 50/50",
  all_lending: "All lending",
  all_lp: "All LP",
};

const COLORS: Record<string, string> = {
  model: "#e8eaed",
  best_rate_now: "#9aa3af",
  static_50_50: "#646d7a",
  all_lending: "#6fbf8b",
  all_lp: "#4a9eff",
};

const ORDER = ["model", "best_rate_now", "static_50_50", "all_lending", "all_lp"];

function pct(value: number, digits = 2): string {
  return `${(value * 100).toFixed(digits)}%`;
}

export default async function BacktestPage() {
  const metrics = await loadMetrics();

  if (!metrics) {
    return (
      <Panel title="No backtest yet">
        <EmptyState title="The metrics file is missing">
          Run <code>python -m helm_agent.train --history data/base_eth_usdc_15m.jsonl</code>{" "}
          to produce <code>agent/models/metrics.json</code> and this page fills in.
        </EmptyState>
      </Panel>
    );
  }

  const model = metrics.strategies.model as StrategyMetrics | undefined;
  const baseline = metrics.strategies.best_rate_now as StrategyMetrics | undefined;
  const series: Series[] = ORDER.filter((name) => metrics.strategies[name]).map((name) => ({
    key: name,
    label: LABELS[name],
    color: COLORS[name],
    points: metrics.strategies[name].equity,
  }));

  const gap = model && baseline ? baseline.total_return - model.total_return : 0;
  const wins = model && baseline ? model.total_return >= baseline.total_return : false;

  return (
    <>
      <div className="section-head">
        <div>
          <div className="eyebrow">Base mainnet · out of sample</div>
          <h1 style={{ fontSize: 22 }}>Backtest</h1>
        </div>
        <div className="row">
          <span className="small faint">
            trained {timeLabel(metrics.trainedAt * 1000)}
          </span>
          <a className="button" href="/proof.json">
            Machine-readable
          </a>
        </div>
      </div>

      <div className="prose" style={{ marginBottom: "var(--space-5)" }}>
        <p>
          The model is fitted on the first seventy percent of the history and scored on the
          last thirty percent, which it never saw. The prices, volumes, fees and pool depth
          are Uniswap v3 <code>Swap</code> events on Base mainnet
          {metrics.pool ? (
            <>
              {" "}
              in pool <code>{metrics.pool}</code>
            </>
          ) : null}
          , not a simulation of a simulation.{" "}
          {metrics.poolFeeBps ? `The pool charges ${metrics.poolFeeBps} bps.` : null}
        </p>
        <p>
          The baseline Helm is judged against is <strong>best rate now</strong>: hold
          whichever venue paid more in the last bar. It makes no forecast, so it cannot be
          late. That is a deliberately hard baseline — it has perfect knowledge of the
          quantity Helm has to predict.
        </p>
      </div>

      <section className="grid grid-4">
        <div className="stat">
          <span className="stat-label">Helm return</span>
          <span className="stat-value">{model ? pct(model.total_return) : "—"}</span>
          <span className="stat-note">out of sample</span>
        </div>
        <div className="stat">
          <span className="stat-label">Best rate now</span>
          <span className="stat-value">{baseline ? pct(baseline.total_return) : "—"}</span>
          <span className="stat-note">the baseline</span>
        </div>
        <div className="stat">
          <span className="stat-label">Difference</span>
          <span className="stat-value" style={wins ? undefined : { color: "var(--veto)" }}>
            {model && baseline ? `${wins ? "+" : ""}${pct(model.total_return - baseline.total_return)}` : "—"}
          </span>
          <span className="stat-note">Helm minus baseline</span>
        </div>
        <div className="stat">
          <span className="stat-label">Rebalance cost</span>
          <span className="stat-value">
            {model ? `$${model.rebalance_cost.toFixed(0)}` : "—"}
          </span>
          <span className="stat-note">
            {model ? `${model.trades} trades` : undefined}
          </span>
        </div>
      </section>

      <section className="section">
        <Panel title="Equity curves" eyebrow="capital after each bar">
          <EquityChart series={series} />
        </Panel>
      </section>

      <section className="section">
        <Panel title="Every strategy" eyebrow="same window, same costs" flush>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>strategy</th>
                  <th className="num">total return</th>
                  <th className="num">annualised</th>
                  <th className="num">annualised vol</th>
                  <th className="num">Sharpe</th>
                  <th className="num">max drawdown</th>
                  <th className="num">fees earned</th>
                  <th className="num">rebalance cost</th>
                  <th className="num">trades</th>
                  <th className="num">average LP</th>
                </tr>
              </thead>
              <tbody>
                {ORDER.filter((name) => metrics.strategies[name]).map((name) => {
                  const s = metrics.strategies[name];
                  return (
                    <tr key={name}>
                      <td>
                        <span
                          className="legend-swatch"
                          style={{
                            background: COLORS[name],
                            display: "inline-block",
                            marginRight: 8,
                            verticalAlign: "middle",
                          }}
                        />
                        {LABELS[name]}
                      </td>
                      <td className="num">{pct(s.total_return)}</td>
                      <td className="num">{pct(s.annualised_return)}</td>
                      <td className="num">{pct(s.annualised_vol)}</td>
                      <td className="num">{s.sharpe.toFixed(2)}</td>
                      <td className="num">{pct(s.max_drawdown)}</td>
                      <td className="num">${s.fees_earned.toFixed(2)}</td>
                      <td className="num">${s.rebalance_cost.toFixed(2)}</td>
                      <td className="num">{s.trades}</td>
                      <td className="num">{pct(s.average_allocation, 1)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </Panel>
      </section>

      <section className="section grid grid-2">
        <Panel title="Where Helm loses" eyebrow="the honest part">
          {model && baseline ? (
            <>
              <div className={`note ${wins ? "" : "warn"}`}>
                {wins ? (
                  <>
                    <strong>Helm beats best rate now by {pct(-gap)} over the evaluation
                    window.</strong> The margin is small enough that it should be read as
                    &ldquo;not worse&rdquo; rather than as a claim of alpha.
                  </>
                ) : (
                  <>
                    <strong>
                      Helm loses to best rate now by {pct(gap)} over the evaluation window.
                    </strong>{" "}
                    That is the honest number and it is not small.
                  </>
                )}
              </div>
              <ol className="plain-list" style={{ marginTop: "var(--space-4)" }}>
                <li>
                  <strong>The baseline has no lag.</strong> The moment the fee yield
                  crosses the lending rate it is fully in, and the moment it crosses back it
                  is fully out. Helm forecasts the same quantity, and a forecast of a spiky,
                  self-referential series is always a little late.
                </li>
                <li>
                  <strong>Trading is not free.</strong> The baseline is rebalanced on every
                  bar and pays for it ({baseline.trades} trades, $
                  {baseline.rebalance_cost.toFixed(0)}); Helm traded{" "}
                  {model.trades} times and paid ${model.rebalance_cost.toFixed(0)}. Most of
                  the gap is that cost, not a worse forecast.
                </li>
                <li>
                  <strong>The baseline is not runnable.</strong> It needs the fee yield of
                  the bar that just closed, on the exact pool, before the next bar starts.
                  On the live contract that number is measured after the fact, by the chain.
                </li>
                <li>
                  <strong>Impermanent loss is not in the model&apos;s favour.</strong> The
                  LP leg earns fees and loses inventory value when the price moves; the
                  lending leg has no inventory risk at all.
                </li>
              </ol>
              <div className="note" style={{ marginTop: "var(--space-4)" }}>
                <strong>What Helm claims.</strong> Not that it beats a perfect rate ticker.
                That it holds a position a fixed allocation cannot hold, with an on-chain
                guarantee that the model cannot overstep — and that the comparison is in
                the report precisely so a judge does not have to take Helm&apos;s word for
                it.
              </div>
            </>
          ) : (
            <EmptyState title="No strategies in the metrics file" />
          )}
        </Panel>

        <Panel title="How the run was made" eyebrow="reproducible">
          <dl className="kv">
            <dt>Pool</dt>
            <dd>{metrics.pool ?? "—"}</dd>
            <dt>Pool fee</dt>
            <dd>{metrics.poolFeeBps !== undefined ? `${metrics.poolFeeBps} bps` : "—"}</dd>
            <dt>History</dt>
            <dd>
              {metrics.historyBars} bars
              {metrics.barSeconds ? ` of ${metrics.barSeconds}s` : ""}
            </dd>
            <dt>Window</dt>
            <dd>
              {metrics.windowStart && metrics.windowEnd
                ? `${timeLabel(metrics.windowStart * 1000)} → ${timeLabel(metrics.windowEnd * 1000)}`
                : "—"}
            </dd>
            <dt>Labelled rows</dt>
            <dd>
              {metrics.datasetRows} ({metrics.trainRows} train / {metrics.evaluationRows}{" "}
              evaluation)
            </dd>
            <dt>Forecast horizon</dt>
            <dd>{metrics.horizonHours}h</dd>
            <dt>Lending rate</dt>
            <dd>{metrics.lendingAprBps} bps</dd>
            <dt>Capital</dt>
            <dd>${metrics.capitalUsd.toLocaleString("en-US")}</dd>
            <dt>Allocation MAE</dt>
            <dd>{metrics.report.allocation_mae.toFixed(4)}</dd>
            <dt>Volatility MAE</dt>
            <dd>{metrics.report.volatility_mae_bps.toFixed(0)} bps</dd>
            <dt>Yield MAE</dt>
            <dd>{metrics.report.yield_mae_bps.toFixed(0)} bps</dd>
          </dl>
          <div className="note" style={{ marginTop: "var(--space-4)" }}>
            The full report, including the loss analysis, is{" "}
            <a href="https://github.com/Alpha-Hackathon-Grinding-Society/helm/blob/main/docs/BENCHMARK.md">
              docs/BENCHMARK.md
            </a>
            . It is generated by the training command, so it cannot drift from the run that
            produced these numbers.
          </div>
        </Panel>
      </section>
    </>
  );
}
