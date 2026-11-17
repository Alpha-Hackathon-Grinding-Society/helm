import Link from "next/link";
import {
  loadCycles,
  loadDeployment,
  loadMetrics,
  type Cycle,
} from "@/lib/deployment";
import { readChainStateWithTimeout } from "@/lib/chain";
import { SplitBar } from "@/components/split-bar";
import {
  AddressLink,
  Badge,
  EmptyState,
  Panel,
  Stat,
  StatusDot,
  TxLink,
  bpsPct,
  pct,
  timeLabel,
  usd,
} from "@/components/bits";

export const dynamic = "force-dynamic";
export const revalidate = 0;

function outcomeOf(cycle: Cycle): { label: string; kind: "ok" | "clamp" | "veto" | "plain" } {
  if (cycle.chain.rejected) return { label: "rejected", kind: "veto" };
  if (cycle.chain.noTrade) return { label: "no trade", kind: "plain" };
  if (cycle.chain.evaluated) {
    const clamped =
      cycle.chain.evaluated.modelLpShareBps !== cycle.chain.evaluated.finalLpShareBps ||
      cycle.chain.evaluated.modelRangeWidthBps !== cycle.chain.evaluated.finalRangeWidthBps;
    return clamped
      ? { label: "clamped", kind: "clamp" }
      : { label: "executed", kind: "ok" };
  }
  return { label: "posted", kind: "plain" };
}

export default async function OverviewPage() {
  const deployment = await loadDeployment();
  const [cycles, metrics, snapshot] = await Promise.all([
    loadCycles(),
    loadMetrics(),
    readChainStateWithTimeout(deployment),
  ]);

  const latest = cycles.length > 0 ? cycles[cycles.length - 1] : null;
  const clampedCycles = cycles.filter((cycle) => {
    const evaluated = cycle.chain.evaluated;
    return (
      evaluated &&
      (evaluated.modelLpShareBps !== evaluated.finalLpShareBps ||
        evaluated.modelRangeWidthBps !== evaluated.finalRangeWidthBps)
    );
  });
  const executedCycles = cycles.filter((cycle) => cycle.chain.rebalance).length;

  const vault = snapshot.vault;
  const reactive = snapshot.reactive;
  const modelStrategy = metrics?.strategies.model;
  const baseline = metrics?.strategies.best_rate_now;

  return (
    <>
      <section className="hero">
        <div>
          <h1 className="hero-title">The model proposes. The contract decides.</h1>
          <p className="hero-sub">
            Every cycle a neural network reads the market and writes down how much of the
            vault it thinks should sit in the liquidity position. That number goes to a{" "}
            <strong>Reactive smart contract on Lasna</strong>, which checks it against
            limits the owner set, refuses anything stale or over-sized, and sends the
            surviving number back to the vault on Base Sepolia. The agent never gets to
            move money itself.
          </p>
          <div className="row" style={{ marginTop: "var(--space-4)" }}>
            <Link className="button primary" href="/cycles">
              Cycle log
            </Link>
            <Link className="button" href="/policy">
              What the contract enforces
            </Link>
            <Link className="button" href="/backtest">
              Backtest vs. best rate now
            </Link>
          </div>
        </div>

        <Panel title="Right now" eyebrow="live chain state">
          {snapshot.errors.length > 0 ? (
            <div className="note error" style={{ marginBottom: "var(--space-3)" }}>
              <strong>Chain read failed.</strong>
              <ul className="plain-list" style={{ marginTop: "var(--space-2)" }}>
                {snapshot.errors.map((error) => (
                  <li key={error}>{error}</li>
                ))}
              </ul>
            </div>
          ) : null}

          {vault ? (
            <dl className="kv">
              <dt>Vault value</dt>
              <dd>{usd(vault.totalValueUsd / 1e18)}</dd>
              <dt>LP / lending</dt>
              <dd>
                {bpsPct(vault.currentLpShareBps)} / {bpsPct(10000 - vault.currentLpShareBps)}
              </dd>
              <dt>Cycles requested</dt>
              <dd>{vault.lastRequestedCycleId}</dd>
              <dt>Cycles executed</dt>
              <dd>{vault.lastExecutedCycleId}</dd>
              <dt>Vault</dt>
              <dd>
                <StatusDot state={vault.paused ? "bad" : "live"}>
                  {vault.paused ? "paused" : "running"}
                </StatusDot>
              </dd>
            </dl>
          ) : (
            <EmptyState title="Vault unread">
              Base Sepolia did not answer. The numbers above are not shown rather than
              guessed.
            </EmptyState>
          )}

          {reactive ? (
            <dl className="kv" style={{ marginTop: "var(--space-4)" }}>
              <dt>Enforcer cycle</dt>
              <dd>
                {reactive.cycleId} <span className="faint">(pending {reactive.pendingCycleId})</span>
              </dd>
              <dt>Fee edge</dt>
              <dd>
                {reactive.feeEdgeMeasured ? `${reactive.feeEdgeBps} bps` : "not measured"}
              </dd>
              <dt>Forecasts graded</dt>
              <dd>{reactive.gradedForecasts}</dd>
              <dt>Enforcer</dt>
              <dd>
                <StatusDot state={reactive.paused ? "bad" : "live"}>
                  {reactive.paused ? "paused" : "running"}
                </StatusDot>
              </dd>
            </dl>
          ) : (
            <EmptyState title="Enforcer unread">
              Reactive Lasna did not answer.
            </EmptyState>
          )}

          <p className="tiny faint" style={{ marginTop: "var(--space-4)" }}>
            Read at {timeLabel(snapshot.fetchedAt)} from {deployment.chain} and{" "}
            {deployment.reactive.network}.
          </p>
        </Panel>
      </section>

      <section className="section">
        <div className="grid grid-4">
          <Stat
            label="Vault value"
            value={vault ? usd(vault.totalValueUsd / 1e18) : "—"}
            note="Base Sepolia, live"
          />
          <Stat
            label="Current LP share"
            value={vault ? bpsPct(vault.currentLpShareBps) : "—"}
            note={vault ? `range ${bpsPct(vault.currentRangeWidthBps)}` : undefined}
          />
          <Stat
            label="Cycles in the log"
            value={cycles.length}
            note={`${executedCycles} executed`}
          />
          <Stat
            label="Clamped by contract"
            value={clampedCycles.length}
            note="model number changed on chain"
          />
        </div>
      </section>

      <section className="section">
        <Panel
          title="The latest cycle"
          eyebrow={latest ? `cycle ${latest.cycleId}` : "no cycles yet"}
          actions={
            latest ? (
              <>
                <Badge kind={outcomeOf(latest).kind}>{outcomeOf(latest).label}</Badge>
                <TxLink
                  href=""
                  hash={latest.posted.txHash}
                  explorer={deployment.explorer}
                />
              </>
            ) : null
          }
        >
          {latest ? (
            <>
              <SplitBar
                modelLpShareBps={latest.proposal.modelAllocationBps}
                finalLpShareBps={
                  latest.chain.evaluated?.finalLpShareBps ??
                  latest.chain.rebalance?.lpShareBps ??
                  latest.proposal.expectedLpShareBps
                }
                minBps={vault?.limits.lpShareMinBps}
                maxBps={vault?.limits.lpShareMaxBps}
                showTicks
                label={`Cycle ${latest.cycleId}`}
              />
              <div className="grid grid-3" style={{ marginTop: "var(--space-4)" }}>
                <div>
                  <div className="eyebrow">model said</div>
                  <div className="num" style={{ fontSize: 18 }}>
                    {bpsPct(latest.proposal.modelAllocationBps)}
                  </div>
                </div>
                <div>
                  <div className="eyebrow">contract enforced</div>
                  <div className="num" style={{ fontSize: 18 }}>
                    {bpsPct(
                      latest.chain.evaluated?.finalLpShareBps ??
                        latest.chain.rebalance?.lpShareBps ??
                        latest.proposal.expectedLpShareBps,
                    )}
                  </div>
                </div>
                <div>
                  <div className="eyebrow">why</div>
                  <div className="small dim">{latest.proposal.rationale}</div>
                </div>
              </div>
            </>
          ) : (
            <EmptyState title="No cycle has run yet">
              The agent writes one line per cycle to <code>agent/ledger/cycles.jsonl</code>.
              Run <code>python -m helm_agent.cli --cycles 12</code> and this page fills in.
            </EmptyState>
          )}
        </Panel>
      </section>

      <section className="section">
        <Panel
          title="Recent cycles"
          eyebrow="agent ledger"
          flush
          actions={
            <Link className="button" href="/cycles">
              All cycles
            </Link>
          }
        >
          {cycles.length === 0 ? (
            <EmptyState title="The ledger is empty">
              Every cycle the agent runs is appended to <code>agent/ledger/cycles.jsonl</code>,
              with the decision request, the proposal, the verdict and the transaction
              hashes.
            </EmptyState>
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th className="num">#</th>
                    <th>outcome</th>
                    <th className="num">model</th>
                    <th className="num">enforced</th>
                    <th>clamp reasons</th>
                    <th>proposal tx</th>
                    <th className="num">open→post</th>
                  </tr>
                </thead>
                <tbody>
                  {cycles
                    .slice(-6)
                    .reverse()
                    .map((cycle) => {
                      const outcome = outcomeOf(cycle);
                      const final =
                        cycle.chain.evaluated?.finalLpShareBps ??
                        cycle.chain.rebalance?.lpShareBps ??
                        cycle.proposal.expectedLpShareBps;
                      const clamped = outcome.kind === "clamp";
                      return (
                        <tr key={cycle.cycleId} data-clamped={clamped ? "true" : "false"}>
                          <td className="num">{cycle.cycleId}</td>
                          <td>
                            <Badge kind={outcome.kind}>{outcome.label}</Badge>
                          </td>
                          <td className="num">{bpsPct(cycle.proposal.modelAllocationBps)}</td>
                          <td className="num">{bpsPct(final)}</td>
                          <td className="small dim">
                            {cycle.proposal.expectedClampMaskName.length > 0
                              ? cycle.proposal.expectedClampMaskName.join(", ")
                              : "—"}
                          </td>
                          <td>
                            <TxLink
                              href=""
                              hash={cycle.posted.txHash}
                              explorer={deployment.explorer}
                            />
                          </td>
                          <td className="num">
                            {cycle.latency?.openToPostMs != null
                              ? `${cycle.latency.openToPostMs}ms`
                              : "—"}
                          </td>
                        </tr>
                      );
                    })}
                </tbody>
              </table>
            </div>
          )}
        </Panel>
      </section>

      <section className="section">
        <div className="grid grid-2">
          <Panel title="Backtest headline" eyebrow="Base mainnet history">
            {modelStrategy && baseline ? (
              <>
                <dl className="kv">
                  <dt>Helm model</dt>
                  <dd className={modelStrategy.total_return >= baseline.total_return ? "" : "veto-text"}>
                    {pct(modelStrategy.total_return)}
                  </dd>
                  <dt>Best rate now</dt>
                  <dd>{pct(baseline.total_return)}</dd>
                  <dt>Difference</dt>
                  <dd>
                    {modelStrategy.total_return >= baseline.total_return ? "+" : ""}
                    {pct(modelStrategy.total_return - baseline.total_return)}
                  </dd>
                  <dt>Rebalance cost</dt>
                  <dd>${modelStrategy.rebalance_cost.toFixed(2)}</dd>
                </dl>
                <div className="note" style={{ marginTop: "var(--space-4)" }}>
                  The model is scored against a baseline that holds whichever venue paid
                  more in the last bar. Where Helm loses, it says so — the{" "}
                  <Link href="/backtest">backtest page</Link> spells out the loss.
                </div>
              </>
            ) : (
              <EmptyState title="No backtest yet">
                Run <code>python -m helm_agent.train</code> to produce{" "}
                <code>agent/models/metrics.json</code>.
              </EmptyState>
            )}
          </Panel>

          <Panel title="Deployment" eyebrow="testnet">
            <dl className="kv">
              <dt>Vault</dt>
              <dd>
                <AddressLink address={deployment.vault} explorer={deployment.explorer} />
              </dd>
              <dt>Enforcer</dt>
              <dd>
                <AddressLink
                  address={deployment.reactive.address}
                  explorer={deployment.reactive.explorer}
                />
              </dd>
              <dt>Agent</dt>
              <dd>
                <AddressLink address={deployment.agent} explorer={deployment.explorer} />
              </dd>
              <dt>Callback proxy</dt>
              <dd>
                <AddressLink
                  address={deployment.callbackProxy}
                  explorer={deployment.explorer}
                />
              </dd>
              <dt>Chain</dt>
              <dd>
                {deployment.chain} · {deployment.chainId}
              </dd>
              <dt>Reactive chain</dt>
              <dd>
                {deployment.reactive.network} · {deployment.reactive.chainId}
              </dd>
            </dl>
          </Panel>
        </div>
      </section>
    </>
  );
}
