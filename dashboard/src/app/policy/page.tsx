import { loadDeployment } from "@/lib/deployment";
import { readChainStateWithTimeout } from "@/lib/chain";
import { AddressLink, Badge, Panel, StatusDot, bpsPct } from "@/components/bits";

export const dynamic = "force-dynamic";
export const revalidate = 0;

const CLAMP_LAYERS = [
  {
    title: "1 · The user's envelope",
    body: "Every proposal is clamped into the LP-share and range-width window the owner approved. A model that asks for 90% LP when the user approved 60% gets 60%, and the clamp is recorded in the event.",
  },
  {
    title: "2 · On-chain volatility exit",
    body: "The contract derives realized volatility from the price path it observes itself. Above the exit level it pulls the vault to 0% LP without asking the model anything. This is the only direction the contract may move on its own, and it only moves toward safety.",
  },
  {
    title: "3 · On-chain economic veto",
    body: "The contract annualises the fee flow it observes in the pool and compares it with the lending rate it observes. If liquidity provisioning does not beat lending by the required margin, the vault is not put into LP at all. An edge it has not measured is not a positive edge.",
  },
];

const REJECTION_RULES = [
  ["Unknown agent", "The proposal did not come from the registered agent address."],
  ["Cycle mismatch", "The proposal answered a cycle that is not the open one."],
  ["Stale", "The proposal arrived after the freshness window closed."],
  ["No limits", "The owner has not approved a risk envelope yet."],
  ["Paused", "The vault is paused."],
  ["Replay", "The cycle was already spent."],
  ["Bad input", "The proposal was malformed, or was prepared before the cycle opened."],
];

export default async function PolicyPage() {
  const deployment = await loadDeployment();
  const snapshot = await readChainStateWithTimeout(deployment);
  const vault = snapshot.vault;
  const reactive = snapshot.reactive;
  const limits = vault?.limits;

  return (
    <>
      <div className="section-head">
        <div>
          <div className="eyebrow">on-chain enforcement</div>
          <h1 style={{ fontSize: 22 }}>What the contract is allowed to do</h1>
        </div>
        <div className="row">
          {reactive ? (
            <StatusDot state={reactive.paused ? "bad" : "live"}>
              enforcer {reactive.paused ? "paused" : "running"}
            </StatusDot>
          ) : null}
          <a
            className="button"
            href={`${deployment.reactive.explorer.replace(/\/$/, "")}/address/${deployment.reactive.address}`}
            target="_blank"
            rel="noreferrer"
          >
            Source on the scan
          </a>
        </div>
      </div>

      <div className="prose" style={{ marginBottom: "var(--space-5)" }}>
        <p>
          The agent can post a number. It cannot move money, and it cannot talk to the
          vault directly: the vault only accepts a rebalance that carries the address of
          the registered enforcer, and only the enforcer asks. Everything below happens
          inside <code>HelmReactive.sol</code> on Lasna, on a copy of the vault state that
          the vault itself mirrors over.
        </p>
      </div>

      <section className="grid grid-3">
        {CLAMP_LAYERS.map((layer) => (
          <Panel key={layer.title} title={layer.title} eyebrow="clamp layer">
            <p className="small dim">{layer.body}</p>
          </Panel>
        ))}
      </section>

      <section className="section grid grid-2">
        <Panel title="The live envelope" eyebrow="read from Base Sepolia">
          {limits ? (
            <dl className="kv">
              <dt>LP share floor</dt>
              <dd>{bpsPct(limits.lpShareMinBps)}</dd>
              <dt>LP share ceiling</dt>
              <dd>{bpsPct(limits.lpShareMaxBps)}</dd>
              <dt>Range width floor</dt>
              <dd>{bpsPct(limits.rangeWidthMinBps)}</dd>
              <dt>Range width ceiling</dt>
              <dd>{bpsPct(limits.rangeWidthMaxBps)}</dd>
              <dt>Cycle cooldown</dt>
              <dd>{limits.cooldownSec}s</dd>
              <dt>Volatility exit</dt>
              <dd>{limits.volExitLevelBps} bps</dd>
              <dt>Minimum trade</dt>
              <dd>{limits.minTradeBps} bps</dd>
              <dt>Freshness window</dt>
              <dd>{limits.freshnessSec}s</dd>
              <dt>Mirrored on Lasna</dt>
              <dd>
                {reactive ? (
                  <Badge kind={reactive.limitsSet ? "ok" : "veto"}>
                    {reactive.limitsSet ? "yes" : "no"}
                  </Badge>
                ) : (
                  "unknown"
                )}
              </dd>
            </dl>
          ) : (
            <p className="small dim">
              The vault did not answer, so the envelope is shown from the deployment record
              rather than from the chain.
            </p>
          )}
          <div className="note" style={{ marginTop: "var(--space-4)" }}>
            The envelope is set by the owner with <code>setLimits</code> on the vault. The
            vault emits <code>LimitsUpdated</code>, the enforcer mirrors it, and the
            enforcer&apos;s copy is the one that clamps. The owner does not have to trust
            the agent to keep the limits: the limits live on chain.
          </div>
        </Panel>

        <Panel title="Why a proposal is thrown away" eyebrow="rejection rules">
          <table>
            <thead>
              <tr>
                <th>rule</th>
                <th>meaning</th>
              </tr>
            </thead>
            <tbody>
              {REJECTION_RULES.map(([name, meaning]) => (
                <tr key={name}>
                  <td style={{ whiteSpace: "nowrap" }}>{name}</td>
                  <td className="small dim">{meaning}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="note" style={{ marginTop: "var(--space-4)" }}>
            The first rule that fires is the reason, and exactly one reason is recorded.
            A rejected proposal never moves money: the vault stays where it was.
          </div>
        </Panel>
      </section>

      <section className="section grid grid-2">
        <Panel title="What the agent can do" eyebrow="and what it cannot">
          <ul className="plain-list">
            <li>
              <strong>Can</strong> read the market, run the model, and post one proposal per
              open cycle to the vault.
            </li>
            <li>
              <strong>Can</strong> be paused, stopped, and have its proposals rejected
              without any of its money moving.
            </li>
            <li>
              <strong>Cannot</strong> call the vault&apos;s rebalance function with its own
              address: the vault checks that the caller is the enforcer.
            </li>
            <li>
              <strong>Cannot</strong> move the LP share outside the owner&apos;s envelope:
              the enforcer clamps, and the agent&apos;s number is overwritten on chain.
            </li>
            <li>
              <strong>Cannot</strong> make the contract trade in a losing market: the
              volatility exit and the economic veto are computed from what the contract
              observed itself.
            </li>
          </ul>
        </Panel>

        <Panel title="Contracts" eyebrow="where the rules live">
          <dl className="kv">
            <dt>Enforcer</dt>
            <dd>
              <AddressLink
                address={deployment.reactive.address}
                explorer={deployment.reactive.explorer}
              />
            </dd>
            <dt>Vault</dt>
            <dd>
              <AddressLink address={deployment.vault} explorer={deployment.explorer} />
            </dd>
            <dt>LP pool</dt>
            <dd>
              <AddressLink address={deployment.lpPool} explorer={deployment.explorer} />
            </dd>
            <dt>Lending market</dt>
            <dd>
              <AddressLink address={deployment.lendingPool} explorer={deployment.explorer} />
            </dd>
            <dt>Callback proxy</dt>
            <dd>
              <AddressLink
                address={deployment.callbackProxy}
                explorer={deployment.explorer}
              />
            </dd>
          </dl>
          <div className="note" style={{ marginTop: "var(--space-4)" }}>
            The enforcer subscribes to the pool, the lending market and the vault directly
            on Base Sepolia, so it reacts to their events without anyone relaying them.
          </div>
        </Panel>
      </section>
    </>
  );
}
