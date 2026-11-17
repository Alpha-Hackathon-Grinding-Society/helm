import type { ReactNode } from "react";

/** A link to a transaction on a block explorer, with the hash shortened for reading. */
export function TxLink({
  href,
  hash,
  explorer,
}: {
  href: string;
  hash: string;
  explorer: string;
}) {
  if (!hash) return <span className="faint">—</span>;
  const url = `${explorer.replace(/\/$/, "")}/tx/${hash}`;
  return (
    <a className="chain-link" href={url} target="_blank" rel="noreferrer">
      {short(hash)}
    </a>
  );
}

/** A link to an address on a block explorer. */
export function AddressLink({
  address,
  explorer,
}: {
  address: string;
  explorer: string;
}) {
  if (!address) return <span className="faint">—</span>;
  const url = `${explorer.replace(/\/$/, "")}/address/${address}`;
  return (
    <a className="chain-link" href={url} target="_blank" rel="noreferrer">
      {short(address)}
    </a>
  );
}

export function short(hash: string): string {
  if (!hash) return "—";
  if (hash.length <= 14) return hash;
  return `${hash.slice(0, 8)}…${hash.slice(-6)}`;
}

export function Stat({
  label,
  value,
  note,
}: {
  label: string;
  value: ReactNode;
  note?: ReactNode;
}) {
  return (
    <div className="stat">
      <span className="stat-label">{label}</span>
      <span className="stat-value">{value}</span>
      {note ? <span className="stat-note">{note}</span> : null}
    </div>
  );
}

export type BadgeKind = "ok" | "clamp" | "veto" | "live" | "plain";

export function Badge({ kind, children }: { kind: BadgeKind; children: ReactNode }) {
  return <span className={`badge ${kind === "plain" ? "" : kind}`}>{children}</span>;
}

/** A live/stale/error indicator that does not rely on colour alone. */
export function StatusDot({
  state,
  children,
}: {
  state: "live" | "warn" | "bad";
  children: ReactNode;
}) {
  return (
    <span className="status">
      <span className={`status-dot ${state === "live" ? "" : state}`} aria-hidden="true" />
      {children}
    </span>
  );
}

export function Panel({
  title,
  eyebrow,
  actions,
  children,
  flush,
}: {
  title: string;
  eyebrow?: string;
  actions?: ReactNode;
  children: ReactNode;
  flush?: boolean;
}) {
  return (
    <section className="panel">
      <div className="panel-head">
        <div>
          {eyebrow ? <div className="eyebrow">{eyebrow}</div> : null}
          <h2>{title}</h2>
        </div>
        {actions ? <div className="row">{actions}</div> : null}
      </div>
      <div className={`panel-body${flush ? " flush" : ""}`}>{children}</div>
    </section>
  );
}

export function EmptyState({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <div className="state">
      <div className="state-title">{title}</div>
      <div>{children}</div>
    </div>
  );
}

export function timeLabel(ms: number): string {
  if (!ms) return "—";
  return new Date(ms).toISOString().replace("T", " ").slice(0, 19) + "Z";
}

export function pct(value: number, digits = 2): string {
  return `${(value * 100).toFixed(digits)}%`;
}

export function usd(value: number): string {
  return `$${value.toLocaleString("en-US", { maximumFractionDigits: 0 })}`;
}

export function bpsPct(value: number, digits = 2): string {
  return `${(value / 100).toFixed(digits)}%`;
}
