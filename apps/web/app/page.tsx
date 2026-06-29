"use client";

import { useEffect, useState } from "react";
import { apiUrl } from "../lib/api";

type Health = {
  status: string;
  service: string;
  checks: Record<string, { status: string }>;
  providers: Record<string, string>;
};

export default function Home() {
  const [health, setHealth] = useState<Health | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(apiUrl("/health"))
      .then((r) => r.json())
      .then(setHealth)
      .catch((e) => setError(String(e)));
  }, []);

  return (
    <main style={{ maxWidth: 720, margin: "0 auto", padding: "3rem 1.5rem" }}>
      <h1 style={{ fontSize: "2rem" }}>TrustStack&nbsp;Lite</h1>
      <p style={{ opacity: 0.8 }}>
        Risk-adaptive onboarding, consent governance, and document verification.
      </p>

      <section
        style={{
          marginTop: "2rem",
          padding: "1.25rem",
          borderRadius: 12,
          background: "#141a30",
          border: "1px solid #243056",
        }}
      >
        <h2 style={{ marginTop: 0, fontSize: "1.1rem" }}>API health</h2>
        {error && <p style={{ color: "#ff6b6b" }}>Cannot reach API: {error}</p>}
        {!health && !error && <p>Loading…</p>}
        {health && (
          <pre style={{ whiteSpace: "pre-wrap", margin: 0 }}>
            {JSON.stringify(health, null, 2)}
          </pre>
        )}
      </section>
    </main>
  );
}
