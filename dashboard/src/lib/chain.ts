/**
 * Live chain state, read with viem.
 *
 * The dashboard shows three different kinds of truth and it is important that they are
 * not confused with each other:
 *
 *  - **chain state** is read live, right now, from the two chains Helm runs on;
 *  - **the cycle log** is the agent's committed record of past cycles;
 *  - **the backtest** is an offline result computed from mainnet history.
 *
 * Nothing here is a fixture. If the chain is unreachable the page says so rather than
 * showing a stale number that looks live.
 */
import { createPublicClient, http, formatUnits, type PublicClient } from "viem";
import { baseSepolia } from "viem/chains";
import type { Deployment, Limits } from "./deployment";

export type VaultState = {
  address: string;
  owner: string;
  agent: string;
  paused: boolean;
  limitsSet: boolean;
  totalValueUsd: number;
  lpShareBps: number;
  lendingShareBps: number;
  currentLpShareBps: number;
  currentRangeWidthBps: number;
  lastRequestedCycleId: number;
  lastExecutedCycleId: number;
  priceE18: number;
  rateBps: number;
  limits: Limits;
};

export type ReactiveState = {
  address: string;
  cycleId: number;
  pendingCycleId: number;
  currentLpShareBps: number;
  volBps: number;
  rateBps: number;
  feeAprBps: number;
  lastExecutedCycleId: number;
  gradedForecasts: number;
  limitsSet: boolean;
  paused: boolean;
  feeEdgeMeasured: boolean;
  feeEdgeBps: number;
};

export type ChainSnapshot = {
  fetchedAt: number;
  vault: VaultState | null;
  reactive: ReactiveState | null;
  errors: string[];
};

const VAULT_ABI = [
  { name: "owner", type: "function", stateMutability: "view", inputs: [], outputs: [{ type: "address" }] },
  { name: "agent", type: "function", stateMutability: "view", inputs: [], outputs: [{ type: "address" }] },
  { name: "paused", type: "function", stateMutability: "view", inputs: [], outputs: [{ type: "bool" }] },
  { name: "limitsSet", type: "function", stateMutability: "view", inputs: [], outputs: [{ type: "bool" }] },
  { name: "totalValueUsd", type: "function", stateMutability: "view", inputs: [], outputs: [{ type: "uint256" }] },
  { name: "lpShareBps", type: "function", stateMutability: "view", inputs: [], outputs: [{ type: "uint256" }] },
  { name: "lendingShareBps", type: "function", stateMutability: "view", inputs: [], outputs: [{ type: "uint256" }] },
  { name: "currentLpShareBps", type: "function", stateMutability: "view", inputs: [], outputs: [{ type: "uint256" }] },
  { name: "currentRangeWidthBps", type: "function", stateMutability: "view", inputs: [], outputs: [{ type: "uint256" }] },
  { name: "lastRequestedCycleId", type: "function", stateMutability: "view", inputs: [], outputs: [{ type: "uint256" }] },
  { name: "lastExecutedCycleId", type: "function", stateMutability: "view", inputs: [], outputs: [{ type: "uint256" }] },
  { name: "priceE18", type: "function", stateMutability: "view", inputs: [], outputs: [{ type: "uint256" }] },
  { name: "rateBps", type: "function", stateMutability: "view", inputs: [], outputs: [{ type: "uint256" }] },
  {
    name: "limits",
    type: "function",
    stateMutability: "view",
    inputs: [],
    outputs: [
      { name: "lpShareMinBps", type: "uint256" },
      { name: "lpShareMaxBps", type: "uint256" },
      { name: "rangeWidthMinBps", type: "uint256" },
      { name: "rangeWidthMaxBps", type: "uint256" },
      { name: "cooldownSec", type: "uint256" },
      { name: "volExitLevelBps", type: "uint256" },
      { name: "minTradeBps", type: "uint256" },
      { name: "freshnessSec", type: "uint256" },
    ],
  },
] as const;

const REACTIVE_ABI = [
  {
    name: "state",
    type: "function",
    stateMutability: "view",
    inputs: [],
    outputs: [
      { name: "cycleId", type: "uint256" },
      { name: "pendingCycleId", type: "uint256" },
      { name: "currentLpShareBps", type: "uint256" },
      { name: "volBps", type: "uint256" },
      { name: "rateBps", type: "uint256" },
      { name: "feeAprBps", type: "uint256" },
      { name: "lastExecutedCycleId", type: "uint256" },
      { name: "gradedForecasts", type: "uint256" },
      { name: "limitsSet", type: "bool" },
      { name: "paused", type: "bool" },
    ],
  },
  { name: "feeEdgeMeasured", type: "function", stateMutability: "view", inputs: [], outputs: [{ type: "bool" }] },
  { name: "feeEdgeBps", type: "function", stateMutability: "view", inputs: [], outputs: [{ type: "uint256" }] },
] as const;

function makeClient(rpcUrl: string): PublicClient {
  return createPublicClient({
    chain: baseSepolia,
    transport: http(rpcUrl, { timeout: 20_000, retryCount: 2 }),
  }) as unknown as PublicClient;
}

export async function readChainState(deployment: Deployment): Promise<ChainSnapshot> {
  const errors: string[] = [];
  let vault: VaultState | null = null;
  let reactive: ReactiveState | null = null;
  const base = makeClient(deployment.rpc);
  try {
    const [owner, agent, paused, limitsSet, totalValueUsd, lpShareBps, lendingShareBps, currentLpShareBps, currentRangeWidthBps, lastRequestedCycleId, lastExecutedCycleId, priceE18, rateBps, limits] =
      await Promise.all([
        base.readContract({ address: deployment.vault as `0x${string}`, abi: VAULT_ABI, functionName: "owner" }),
        base.readContract({ address: deployment.vault as `0x${string}`, abi: VAULT_ABI, functionName: "agent" }),
        base.readContract({ address: deployment.vault as `0x${string}`, abi: VAULT_ABI, functionName: "paused" }),
        base.readContract({ address: deployment.vault as `0x${string}`, abi: VAULT_ABI, functionName: "limitsSet" }),
        base.readContract({ address: deployment.vault as `0x${string}`, abi: VAULT_ABI, functionName: "totalValueUsd" }),
        base.readContract({ address: deployment.vault as `0x${string}`, abi: VAULT_ABI, functionName: "lpShareBps" }),
        base.readContract({ address: deployment.vault as `0x${string}`, abi: VAULT_ABI, functionName: "lendingShareBps" }),
        base.readContract({ address: deployment.vault as `0x${string}`, abi: VAULT_ABI, functionName: "currentLpShareBps" }),
        base.readContract({ address: deployment.vault as `0x${string}`, abi: VAULT_ABI, functionName: "currentRangeWidthBps" }),
        base.readContract({ address: deployment.vault as `0x${string}`, abi: VAULT_ABI, functionName: "lastRequestedCycleId" }),
        base.readContract({ address: deployment.vault as `0x${string}`, abi: VAULT_ABI, functionName: "lastExecutedCycleId" }),
        base.readContract({ address: deployment.vault as `0x${string}`, abi: VAULT_ABI, functionName: "priceE18" }),
        base.readContract({ address: deployment.vault as `0x${string}`, abi: VAULT_ABI, functionName: "rateBps" }),
        base.readContract({ address: deployment.vault as `0x${string}`, abi: VAULT_ABI, functionName: "limits" }),
      ]);

    vault = {
      address: deployment.vault.toLowerCase(),
      owner: owner as string,
      agent: agent as string,
      paused: paused as boolean,
      limitsSet: limitsSet as boolean,
      totalValueUsd: Number(totalValueUsd),
      lpShareBps: Number(lpShareBps),
      lendingShareBps: Number(lendingShareBps),
      currentLpShareBps: Number(currentLpShareBps),
      currentRangeWidthBps: Number(currentRangeWidthBps),
      lastRequestedCycleId: Number(lastRequestedCycleId),
      lastExecutedCycleId: Number(lastExecutedCycleId),
      priceE18: Number(priceE18),
      rateBps: Number(rateBps),
      limits: {
        lpShareMinBps: Number(limits[0]),
        lpShareMaxBps: Number(limits[1]),
        rangeWidthMinBps: Number(limits[2]),
        rangeWidthMaxBps: Number(limits[3]),
        cooldownSec: Number(limits[4]),
        volExitLevelBps: Number(limits[5]),
        minTradeBps: Number(limits[6]),
        freshnessSec: Number(limits[7]),
      },
    };
  } catch (error) {
    errors.push(`vault on Base Sepolia: ${(error as Error).message}`);
  }

  // Lasna is not a viem chain we have registered, so it is read as a plain chain id.
  const lasna = createPublicClient({
    chain: {
      id: deployment.reactive.chainId,
      name: deployment.reactive.network,
      nativeCurrency: { name: "lREACT", symbol: "lREACT", decimals: 18 },
      rpcUrls: { default: { http: [deployment.reactive.rpc] } },
    },
    transport: http(deployment.reactive.rpc, { timeout: 20_000, retryCount: 2 }),
  }) as unknown as PublicClient;

  try {
    const [state, feeEdgeMeasured, feeEdgeBps] = await Promise.all([
      lasna.readContract({
        address: deployment.reactive.address as `0x${string}`,
        abi: REACTIVE_ABI,
        functionName: "state",
      }),
      lasna.readContract({
        address: deployment.reactive.address as `0x${string}`,
        abi: REACTIVE_ABI,
        functionName: "feeEdgeMeasured",
      }),
      lasna.readContract({
        address: deployment.reactive.address as `0x${string}`,
        abi: REACTIVE_ABI,
        functionName: "feeEdgeBps",
      }),
    ]);

    reactive = {
      address: deployment.reactive.address.toLowerCase(),
      cycleId: Number(state[0]),
      pendingCycleId: Number(state[1]),
      currentLpShareBps: Number(state[2]),
      volBps: Number(state[3]),
      rateBps: Number(state[4]),
      feeAprBps: Number(state[5]),
      lastExecutedCycleId: Number(state[6]),
      gradedForecasts: Number(state[7]),
      limitsSet: Boolean(state[8]),
      paused: Boolean(state[9]),
      feeEdgeMeasured: Boolean(feeEdgeMeasured),
      feeEdgeBps: Number(feeEdgeBps),
    };
  } catch (error) {
    errors.push(`enforcer on Lasna: ${(error as Error).message}`);
  }

  return { fetchedAt: Date.now(), vault, reactive, errors };
}

/**
 * Read the chain, but never hang the page.
 *
 * A public RPC endpoint that is slow must not turn into a dashboard that never
 * renders. If the chain does not answer within the deadline the page says the chain
 * was unreachable instead of showing a stale number dressed up as a live one.
 */
export async function readChainStateWithTimeout(
  deployment: Deployment,
  timeoutMs = 20_000,
): Promise<ChainSnapshot> {
  let timer: ReturnType<typeof setTimeout> | undefined;
  const deadline = new Promise<ChainSnapshot>((resolve) => {
    timer = setTimeout(
      () =>
        resolve({
          fetchedAt: Date.now(),
          vault: null,
          reactive: null,
          errors: [`the chains did not answer within ${Math.round(timeoutMs / 1000)}s`],
        }),
      timeoutMs,
    );
  });
  try {
    return await Promise.race([readChainState(deployment), deadline]);
  } catch (error) {
    return {
      fetchedAt: Date.now(),
      vault: null,
      reactive: null,
      errors: [(error as Error).message],
    };
  } finally {
    if (timer) clearTimeout(timer);
  }
}

export function usd(value: number): string {
  return `$${formatUnits(BigInt(Math.round(value)), 18)}`;
}

export function bps(value: number): string {
  return `${(value / 100).toFixed(2)}%`;
}
