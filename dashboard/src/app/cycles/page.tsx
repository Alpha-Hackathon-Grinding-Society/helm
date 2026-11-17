import Link from "next/link";
import { loadChainCycles, loadCycles, loadDeployment } from "@/lib/deployment";
import { clampNames, rejectNames } from "@/lib/clamps";
import { SplitBar } from "@/components/split-bar";
import { Badge, EmptyState, Panel, TxLink, bpsPct, timeLabel } from "@/components/bits";

export const dynamic = "force-dynamic";
export const revalidate = 0;

type Outcome = { label: string; kind: "ok" | "clamp" | "veto" | "plain" };

function outcomeOf(cycle: {
  chain: {
    evaluated?: { modelLpShareBps: number; finalLpShareBps: number; modelRangeWidthBps: number; finalRangeWidthBps: number };
    rejected?: unknown;
    noTrade?: unknown;
    rebalance?: unknown;
  };
}): Outcome {
  if (cycle.chain.rejected) return { label: "rejected", kind: "veto" };
  if (cycle.chain.noTrade) return { label: "no trade", kind: "plain" };
  if (cycle.chain.evaluated) {
    const e = cycle.chain.evaluated;
    const clamped =
      e.modelLpShareBps !== e.finalLpShareBps || e.modelRangeWidthBps !== e.finalRangeWidthBps;
    return clamped ? { label: "clamped", kind: "clamp" } : { label: "executed", kind: "ok" };
  }
  return { label: "posted", kind: "plain" };
}

export default async function CyclesPage() {
  const deployment = await loadDeployment();
  const cycles = await loadCycles();
  const chainCycles = await loadChainCycles();
  const clampedCount = cycles.filter((c) => outcomeOf(c).kind === "clamp").length;

  const chainSummary = {
    cycles: chainCycles.length,
    full: chainCycles.filter((c) => c.fullCycle).length,
    clamped: chainCycles.filter((c) => c.evaluated && c.evaluated.clampMask !== 0).length,
    vetoed: chainCycles.filter(
      (c) => c.evaluated && (c.evaluated.clampMask & (1 << 5)) !== 0,
    ).length,
    rejected: chainCycles.filter((c) => c.rejected).length,
    exits: chainCycles.filter((c) => c.autonomousExit).length,
    moved: chainCycles.filter((c) => c.rebalanced).length,
  };

  return (
    <>
      <div className="section-head">
        <div>
          <div className="eyebrow">agent ledger · agent/ledger/cycles.jsonl</div>
          <h1 style={{ fontSize: 22 }}>Cycle log</h1>
        </div>
        <div className="row">
          <Badge kind="plain">{cycles.length} cycles</Badge>
          <Badge kind="clamp">{clampedCount} clamped</Badge>
          <a className="button" href="/proof.json">
            Machine-readable
          </a>
        </div>
      </div>

      {cycles.length === 0 ? (
        <Panel title="Nothing logged yet">
          <EmptyState title="The ledger is empty">
            The agent writes one JSON object per cycle to{" "}
            <code>agent/ledger/cycles.jsonl</code>. Each entry carries the cycle id, the
            decision-request transaction, the raw model number, the contract&apos;s
            verdict and the transaction hash of the rebalance.
          </EmptyState>
        </Panel>
      ) : (
        <div className="stack">
          {cycles
            .slice()
            .reverse()
            .map((cycle) => {
              const outcome = outcomeOf(cycle);
              const final =
                cycle.chain.evaluated?.finalLpShareBps ??
                cycle.chain.rebalance?.lpShareBps ??
                cycle.proposal.expectedLpShareBps;
              const model = cycle.proposal.modelAllocationBps;
              return (
                <Panel
                  key={cycle.cycleId}
                  title={`Cycle ${cycle.cycleId}`}
                  eyebrow={`opened ${timeLabel(cycle.openedAt)}`}
                  actions={
                    <>
                      <Badge kind={outcome.kind}>{outcome.label}</Badge>
                      <TxLink
                        href=""
                        hash={cycle.posted.txHash}
                        explorer={deployment.explorer}
                      />
                    </>
                  }
                >
                  <SplitBar
                    modelLpShareBps={model}
                    finalLpShareBps={final}
                    label={`Cycle ${cycle.cycleId}`}
                  />

                  <div className="table-wrap" style={{ marginTop: "var(--space-4)" }}>
                    <table>
                      <tbody>
                        <tr>
                          <td className="eyebrow">model number</td>
                          <td className="num">{bpsPct(model)}</td>
                          <td className="eyebrow">enforced</td>
                          <td className="num">{bpsPct(final)}</td>
                          <td className="eyebrow">range</td>
                          <td className="num">
                            {bpsPct(cycle.chain.evaluated?.finalRangeWidthBps ?? cycle.proposal.expectedRangeWidthBps)}
                          </td>
                        </tr>
                        <tr>
                          <td className="eyebrow">clamp mask</td>
                          <td className="num">
                            {cycle.chain.evaluated?.clampMask ?? cycle.proposal.expectedClampMask}
                          </td>
                          <td className="eyebrow">reasons</td>
                          <td colSpan={3} className="small dim">
                            {cycle.chain.rejected
                              ? `refused: ${rejectNames(cycle.chain.rejected.reason).join(", ")}`
                              : cycle.chain.evaluated
                                ? clampNames(cycle.chain.evaluated.clampMask).join(", ") ||
                                  "none — the model was inside the envelope"
                                : cycle.proposal.expectedClampMaskName.length > 0
                                  ? `expected: ${cycle.proposal.expectedClampMaskName.join(", ")}`
                                  : "none — the model was inside the envelope"}
                          </td>
                        </tr>
                        <tr>
                          <td className="eyebrow">decision request</td>
                          <td className="num">
                            <TxLink
                              href=""
                              hash={cycle.decisionRequestTx}
                              explorer={deployment.explorer}
                            />
                          </td>
                          <td className="eyebrow">verdict</td>
                          <td className="num">
                            {cycle.chain.evaluated?.txHash ? (
                              <TxLink
                                href=""
                                hash={cycle.chain.evaluated.txHash}
                                explorer={deployment.reactive.explorer}
                              />
                            ) : cycle.chain.rejected?.txHash ? (
                              <TxLink
                                href=""
                                hash={cycle.chain.rejected.txHash}
                                explorer={deployment.reactive.explorer}
                              />
                            ) : (
                              "—"
                            )}
                          </td>
                          <td className="eyebrow">rebalance</td>
                          <td className="num">
                            {cycle.chain.rebalance?.transactionHash ? (
                              <TxLink
                                href=""
                                hash={cycle.chain.rebalance.transactionHash}
                                explorer={deployment.explorer}
                              />
                            ) : (
                              "—"
                            )}
                          </td>
                        </tr>
                        <tr>
                          <td className="eyebrow">latency open→post</td>
                          <td className="num">
                            {cycle.latency?.openToPostMs != null
                              ? `${cycle.latency.openToPostMs}ms`
                              : "—"}
                          </td>
                          <td className="eyebrow">open→verdict</td>
                          <td className="num">
                            {cycle.latency?.openToEvaluatedMs != null
                              ? `${cycle.latency.openToEvaluatedMs}ms`
                              : "—"}
                          </td>
                          <td className="eyebrow">explanation</td>
                          <td className="num small dim">{cycle.explanation.source}</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>

                  <div className="note" style={{ marginTop: "var(--space-4)" }}>
                    <strong>Model rationale.</strong> {cycle.proposal.rationale}
                    {cycle.explanation.text ? (
                      <>
                        <br />
                        {cycle.explanation.text}
                      </>
                    ) : null}
                  </div>
                </Panel>
              );
            })}
        </div>
      )}

      <p className="small faint" style={{ marginTop: "var(--space-5)" }}>
        The same records are committed to the repository, so this page can be checked
        against the file with <code>git log -p agent/ledger/cycles.jsonl</code>.{" "}
        <Link href="/policy">What the contract checked on each cycle →</Link>
      </p>

      <div className="section-head" style={{ marginTop: "var(--space-6)" }}>
        <div>
          <div className="eyebrow">read back from both chains · agent/ledger/chain-events.jsonl</div>
          <h1 style={{ fontSize: 22 }}>What the chains recorded</h1>
        </div>
        <div className="row">
          <Badge kind="plain">{chainSummary.cycles} cycles</Badge>
          <Badge kind="ok">{chainSummary.full} full</Badge>
          <Badge kind="clamp">{chainSummary.clamped} clamped</Badge>
          <Badge kind="veto">{chainSummary.vetoed} vetoed</Badge>
        </div>
      </div>

      {chainCycles.length === 0 ? (
        <Panel title="Nothing read back yet">
          <EmptyState title="No chain record">
            <code>scripts/collect-evidence.py</code> reads both chains and writes
            <code>agent/ledger/chain-events.jsonl</code>. Run it to fill this in.
          </EmptyState>
        </Panel>
      ) : (
        <>
          <p className="small dim" style={{ marginBottom: "var(--space-4)" }}>
            The agent&apos;s ledger above is what the agent believes happened. This is what
            the chains say, read straight off them. They agree on every cycle the agent
            answered; this view also shows the cycles the agent did not answer — including
            the one the contract closed on its own.
          </p>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Cycle</th>
                  <th>Outcome</th>
                  <th>Model → enforced</th>
                  <th>Reason</th>
                  <th>Opened</th>
                  <th>Result</th>
                </tr>
              </thead>
              <tbody>
                {chainCycles
                  .slice()
                  .reverse()
                  .map((cycle) => {
                    const evaluated = cycle.evaluated;
                    const resultTx = cycle.rebalanced?.txHash ?? cycle.noTrade?.txHash ?? cycle.rejected?.txHash;
                    const resultExplorer = cycle.rebalanced ? deployment.explorer : deployment.reactive.explorer;
                    const reason = cycle.rejected
                      ? `refused: ${cycle.rejected.reasonNames.join(", ")}`
                      : cycle.autonomousExit
                        ? `the contract measured ${cycle.autonomousExit.volBps} bps of volatility, over the exit level`
                        : evaluated
                          ? evaluated.clampNames.join(", ") || "none — the model was inside the envelope"
                          : cycle.expired
                            ? `expired after ${cycle.expired.waitedSec}s without an answer`
                            : "open";
                    return (
                      <tr key={cycle.cycleId}>
                        <td className="num">{cycle.cycleId}</td>
                        <td>
                          <Badge
                            kind={
                              cycle.rejected || cycle.evaluated?.clampMask === 33
                                ? "veto"
                                : evaluated?.clampMask
                                  ? "clamp"
                                  : cycle.rebalanced
                                    ? "ok"
                                    : "plain"
                            }
                          >
                            {cycle.outcome.replace("_", " ")}
                          </Badge>
                        </td>
                        <td className="num">
                          {evaluated
                            ? `${bpsPct(evaluated.modelLpShareBps)} → ${bpsPct(evaluated.finalLpShareBps)}`
                            : cycle.posted
                              ? `${bpsPct(cycle.posted.lpShareBps)} → refused`
                              : "—"}
                        </td>
                        <td className="small dim">{reason}</td>
                        <td>
                          {cycle.opened ? (
                            <TxLink
                              href=""
                              hash={cycle.opened.txHash}
                              explorer={deployment.reactive.explorer}
                            />
                          ) : (
                            <span className="faint">—</span>
                          )}
                        </td>
                        <td>
                          {resultTx ? (
                            <TxLink href="" hash={resultTx} explorer={resultExplorer} />
                          ) : cycle.autonomousExit ? (
                            <TxLink
                              href=""
                              hash={cycle.autonomousExit.txHash}
                              explorer={deployment.reactive.explorer}
                            />
                          ) : (
                            <span className="faint">—</span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
              </tbody>
            </table>
          </div>
        </>
      )}
    </>
  );
}
