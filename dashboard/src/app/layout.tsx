import type { Metadata } from "next";
import type { ReactNode } from "react";
import { Nav } from "@/components/nav";
import "./globals.css";

export const metadata: Metadata = {
  title: "Helm — the model proposes, the contract decides",
  description:
    "Helm is a stablecoin fund manager: a neural network proposes an allocation every cycle and a Reactive smart contract decides whether it is allowed to happen.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="shell">
          <header className="masthead">
            <div className="masthead-row">
              <div>
                <div className="wordmark">
                  <h1>Helm</h1>
                  <span className="tag">Reactive × AI</span>
                </div>
                <p className="tagline">
                  A stablecoin fund manager where a neural network proposes the allocation
                  and a Reactive smart contract decides whether it is allowed to happen.
                </p>
              </div>
            </div>
            <Nav />
          </header>

          <main>{children}</main>

          <footer className="footer">
            <span>Helm · Base Sepolia + Reactive Lasna · testnet</span>
            <span>
              Machine-readable proof: <a href="/proof.json">/proof.json</a>
            </span>
          </footer>
        </div>
      </body>
    </html>
  );
}
