/**
 * Where Helm is deployed, and what the dashboard is allowed to show.
 *
 * The addresses come from `deployments/base-sepolia.json`, the file the deployment
 * script writes. The dashboard reads that same file rather than keeping its own copy
 * of the addresses, so there is exactly one place where a deployed address is written
 * down and a judge can check the dashboard against the deployment record.
 */
import { readFile } from "node:fs/promises";
import path from "node:path";

export type Deployment = {
  chainId: number;
  chain: string;
  rpc: string;
  explorer: string;
  deployer: string;
  agent: string;
  token: string;
  lpPool: string;
  lendingPool: string;
  vault: string;
  callbackProxy: string;
  limits: Record<string, number>;
  reactive: {
    network: string;
    chainId: number;
    rpc: string;
    explorer: string;
    address: string;
  };
};

export type Limits = {
  lpShareMinBps: number;
  lpShareMaxBps: number;
  rangeWidthMinBps: number;
  rangeWidthMaxBps: number;
  cooldownSec: number;
  volExitLevelBps: number;
  minTradeBps: number;
  freshnessSec: number;
};

export const REPO_ROOT = path.resolve(process.cwd(), "..");
export const DEPLOYMENT_PATH = path.join(REPO_ROOT, "deployments", "base-sepolia.json");
export const LEDGER_PATH = path.join(REPO_ROOT, "agent", "ledger", "cycles.jsonl");
export const CHAIN_EVENTS_PATH = path.join(REPO_ROOT, "agent", "ledger", "chain-events.jsonl");
export const METRICS_PATH = path.join(REPO_ROOT, "agent", "models", "metrics.json");
export const BENCHMARK_PATH = path.join(REPO_ROOT, "docs", "BENCHMARK.md");

export async function loadDeployment(): Promise<Deployment> {
  const raw = await readFile(DEPLOYMENT_PATH, "utf8");
  return JSON.parse(raw) as Deployment;
}

/**
 * One cycle from the agent's ledger.
 *
 * The ledger is the agent's own record of what it did and what the chain did about it.
 * It is committed to the repository, so the dashboard's cycle log is evidence a judge
 * can diff against the repository, not a render of a database that only exists on
 * somebody's laptop.
 */
export type Cycle = {
  cycleId: number;
  openedAt: number;
  decisionRequestTx: string;
  decisionRequestBlock: number;
  market: {
    priceE18: number;
    rateBps: number;
    volBps: number;
    currentLpShareBps: number;
    totalValueUsd: number;
  };
  model: {
    allocation: number;
    forecastVolBps: number;
    forecastYieldBps: number;
    features: Record<string, number>;
    historyBars: number;
    lastBarTs: number;
  };
  proposal: {
    cycleId: number;
    lpShareBps: number;
    rangeWidthBps: number;
    forecastVolBps: number;
    forecastYieldBps: number;
    modelAllocationBps: number;
    rationale: string;
    expectedLpShareBps: number;
    expectedRangeWidthBps: number;
    expectedClampMask: number;
    expectedClampMaskName: string[];
    expectedNoTrade: boolean;
    source: string;
  };
  explanation: {
    text: string;
    source: string;
    model: string;
    costUsd: number;
    paymentTx: string;
    latencyMs: number;
    error: string;
  };
  posted: {
    txHash: string;
    at: number;
    agent: string;
  };
  chain: {
    evaluated?: {
      modelLpShareBps: number;
      finalLpShareBps: number;
      modelRangeWidthBps: number;
      finalRangeWidthBps: number;
      clampMask: number;
      evaluatedAt: number;
      txHash: string;
      blockNumber: number;
    };
    rejected?: {
      reason: number;
      proposer: string;
      txHash: string;
      blockNumber: number;
    };
    noTrade?: {
      currentLpShareBps: number;
      targetLpShareBps: number;
      clampMask: number;
      txHash: string;
      blockNumber: number;
    };
    rebalance?: {
      cycleId: number;
      lpShareBps: number;
      rangeWidthBps: number;
      lpValueUsd: number;
      totalValueUsd: number;
      action: number;
      clampMask: number;
      blockNumber: number;
      transactionHash: string;
    };
  };
  latency?: {
    openToPostMs?: number | null;
    openToEvaluatedMs?: number;
  };
};

export async function loadCycles(): Promise<Cycle[]> {
  let raw: string;
  try {
    raw = await readFile(LEDGER_PATH, "utf8");
  } catch {
    return [];
  }
  const cycles: Cycle[] = [];
  for (const line of raw.split("\n")) {
    const trimmed = line.trim();
    if (!trimmed) continue;
    try {
      cycles.push(JSON.parse(trimmed) as Cycle);
    } catch {
      // a partially written line is skipped rather than failing the whole page
    }
  }
  return cycles.sort((a, b) => a.cycleId - b.cycleId);
}

/**
 * One cycle as the chains recorded it.
 *
 * `agent/ledger/chain-events.jsonl` is written by `scripts/collect-evidence.py`, which
 * reads both chains and joins their events by cycle id. It is the same file
 * `docs/EVIDENCE.md` is generated from, so the dashboard and the documentation can never
 * disagree about what happened.
 */
export type ChainCycle = {
  cycleId: number;
  outcome: string;
  fullCycle: boolean;
  opened?: { priceE18: number; rateBps: number; volBps: number; openedAt: number; blockNumber: number; txHash: string };
  expired?: { waitedSec: number; blockNumber: number; txHash: string };
  requested?: {
    priceE18: number;
    rateBps: number;
    volBps: number;
    currentLpShareBps: number;
    totalValueUsd: number;
    requestedAt: number;
    blockNumber: number;
    txHash: string;
  };
  posted?: {
    proposer: string;
    lpShareBps: number;
    rangeWidthBps: number;
    forecastVolBps: number;
    forecastYieldBps: number;
    proposedAt: number;
    blockNumber: number;
    txHash: string;
  };
  evaluated?: {
    modelLpShareBps: number;
    finalLpShareBps: number;
    modelRangeWidthBps: number;
    finalRangeWidthBps: number;
    clampMask: number;
    clampNames: string[];
    evaluatedAt: number;
    blockNumber: number;
    txHash: string;
  };
  rejected?: {
    reason: number;
    reasonNames: string[];
    proposer: string;
    blockNumber: number;
    txHash: string;
  };
  noTrade?: {
    currentLpShareBps: number;
    targetLpShareBps: number;
    clampMask: number;
    clampNames: string[];
    blockNumber: number;
    txHash: string;
  };
  rebalanceRequested?: {
    lpShareBps: number;
    rangeWidthBps: number;
    action: number;
    clampMask: number;
    requestedAt: number;
    blockNumber: number;
    txHash: string;
  };
  rebalanced?: {
    lpShareBps: number;
    rangeWidthBps: number;
    lpValueUsd: number;
    totalValueUsd: number;
    action: number;
    clampMask: number;
    clampNames: string[];
    blockNumber: number;
    txHash: string;
    timestamp?: number;
  };
  autonomousExit?: { volBps: number; rangeWidthBps: number; exitedAt: number; blockNumber: number; txHash: string };
  forecastGraded?: {
    volErrBps: number;
    rateErrBps: number;
    realizedVolBps: number;
    realizedRateBps: number;
    blockNumber: number;
    txHash: string;
  };
};

export async function loadChainCycles(): Promise<ChainCycle[]> {
  let raw: string;
  try {
    raw = await readFile(CHAIN_EVENTS_PATH, "utf8");
  } catch {
    return [];
  }
  const cycles: ChainCycle[] = [];
  for (const line of raw.split("\n")) {
    const trimmed = line.trim();
    if (!trimmed) continue;
    try {
      cycles.push(JSON.parse(trimmed) as ChainCycle);
    } catch {
      // a partially written line is skipped rather than failing the whole page
    }
  }
  return cycles.sort((a, b) => a.cycleId - b.cycleId);
}

export type StrategyMetrics = {
  name: string;
  total_return: number;
  annualised_return: number;
  annualised_vol: number;
  sharpe: number;
  max_drawdown: number;
  calmar: number;
  fees_earned: number;
  rebalance_cost: number;
  trades: number;
  average_allocation: number;
  equity: number[];
};

export type ModelMetrics = {
  trainedAt: number;
  historyBars: number;
  barSeconds?: number;
  pool?: string;
  poolFeeBps?: number;
  windowStart?: number;
  windowEnd?: number;
  datasetRows: number;
  trainRows: number;
  evaluationRows: number;
  featureNames: string[];
  labelNames: string[];
  lendingAprBps: number;
  capitalUsd: number;
  rebalanceCostBps: number;
  horizonHours: number;
  report: {
    epochs: number;
    train_loss: number;
    valid_loss: number;
    allocation_mae: number;
    volatility_mae_bps: number;
    yield_mae_bps: number;
    history: { epoch: number; train_loss: number; valid_loss: number }[];
  };
  strategies: Record<string, StrategyMetrics>;
};

export async function loadMetrics(): Promise<ModelMetrics | null> {
  try {
    const raw = await readFile(METRICS_PATH, "utf8");
    return JSON.parse(raw) as ModelMetrics;
  } catch {
    return null;
  }
}
