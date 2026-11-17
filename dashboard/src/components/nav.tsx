"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/", label: "Overview" },
  { href: "/cycles", label: "Cycles" },
  { href: "/policy", label: "Policy" },
  { href: "/backtest", label: "Backtest" },
];

export function Nav() {
  const pathname = usePathname();
  return (
    <nav className="nav" aria-label="Sections">
      {LINKS.map((link) => {
        const current =
          link.href === "/" ? pathname === "/" : pathname.startsWith(link.href);
        return (
          <Link key={link.href} href={link.href} aria-current={current ? "page" : undefined}>
            {link.label}
          </Link>
        );
      })}
    </nav>
  );
}
