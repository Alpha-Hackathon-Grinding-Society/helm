import { NextResponse } from "next/server";
import { loadChainCycles, loadCycles, loadDeployment, loadMetrics } from "@/lib/deployment";
import { readChainStateWithTimeout } from "@/lib/chain";

export const dynamic = "force-dynamic";
export const revalidate = 0;

/**
 * Helm's proof bundle.
 *
 * One JSON document with the deployment record, the live chain state, every cycle in the
 * agent's ledger with its transaction hashes, the same cycles read back off both chains,
 * and the backtest summary. A judge can curl this and then check every hash against the
 * block explorer without trusting the dashboard's rendering of them.
 */
export async function GET() {
  const deployment = await loadDeployment();
  const [cycles, chainCycles, metrics, snapshot] = await Promise.all([
    loadCycles(),
    loadChainCycles(),
    loadMetrics(),
    readChainStateWithTimeout(deployment),
  ]);

  const strategies = metrics
    ? Object.fromEntries(
        Object.entries(metrics.strategies).map(([name, result]) => [
          name,
          {
            totalReturn: result.total_return,
            annualisedReturn: result.annualised_return,
            annualisedVol: result.annualised_vol,
            sharpe: result.sharpe,
            maxDrawdown: result.max_drawdown,
            trades: result.trades,
            averageAllocation: result.average_allocation,
            rebalanceCost: result.rebalance_cost,
            feesEarned: result.fees_earned,
          },
        ]),
      )
    : null;

  const clamped = cycles.filter((cycle) => {
    const evaluated = cycle.chain.evaluated;
    return (
      evaluated &&
      (evaluated.modelLpShareBps !== evaluated.finalLpShareBps ||
        evaluated.modelRangeWidthBps !== evaluated.finalRangeWidthBps)
    );
  });

  return NextResponse.json(
    {
      generatedAt: new Date().toISOString(),
      project: "Helm",
      tagline: "The model proposes. The contract decides.",
      deployment,
      live: snapshot,
      cycles: {
        count: cycles.length,
        clampedCount: clamped.length,
        executedCount: cycles.filter((cycle) => cycle.chain.rebalance).length,
        log: cycles,
      },
      onChain: {
        cycles: chainCycles.length,
        fullCycles: chainCycles.filter((cycle) => cycle.fullCycle).length,
        clampedCount: chainCycles.filter((cycle) => cycle.evaluated && cycle.evaluated.clampMask !== 0).length,
        economicVetoCount: chainCycles.filter(
          (cycle) => cycle.evaluated && (cycle.evaluated.clampMask & (1 << 5)) !== 0,
        ).length,
        rejectedCount: chainCycles.filter((cycle) => cycle.rejected).length,
        autonomousExitCount: chainCycles.filter((cycle) => cycle.autonomousExit).length,
        rebalanceCount: chainCycles.filter((cycle) => cycle.rebalanced).length,
        log: chainCycles,
      },
      backtest: metrics
        ? {
            trainedAt: metrics.trainedAt,
            pool: metrics.pool ?? null,
            poolFeeBps: metrics.poolFeeBps ?? null,
            historyBars: metrics.historyBars,
            barSeconds: metrics.barSeconds ?? null,
            windowStart: metrics.windowStart ?? null,
            windowEnd: metrics.windowEnd ?? null,
            datasetRows: metrics.datasetRows,
            trainRows: metrics.trainRows,
            evaluationRows: metrics.evaluationRows,
            horizonHours: metrics.horizonHours,
            lendingAprBps: metrics.lendingAprBps,
            capitalUsd: metrics.capitalUsd,
            report: metrics.report,
            strategies,
          }
        : null,
    },
    { headers: { "cache-control": "no-store" } },
  );
}
