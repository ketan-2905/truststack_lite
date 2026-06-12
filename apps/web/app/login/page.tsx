"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { login } from "../../lib/api";
import { ErrorBanner } from "../../components/ErrorBanner";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [tenantSlug, setTenantSlug] = useState("acme");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      await login(email, password, tenantSlug);
      router.push("/dashboard");
    } catch (err) {
      setError((err as any).message || "Login failed. Check credentials.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ maxWidth: "400px", margin: "4rem auto" }}>
      <h1 style={{ fontSize: "1.8rem", marginBottom: "2rem", textAlign: "center" }}>TrustStack Lite Login</h1>

      {error && <ErrorBanner error={error} onDismiss={() => setError(null)} />}

      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: "1.5rem" }}>
          <label htmlFor="email" style={{ display: "block", marginBottom: "0.5rem", fontWeight: 500 }}>
            Email
          </label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            style={{
              width: "100%",
              padding: "0.75rem",
              borderRadius: "4px",
              border: "1px solid #555",
              background: "#1a1a1a",
              color: "#e6e9f0",
              boxSizing: "border-box",
            }}
            placeholder="admin@truststack.local"
          />
        </div>

        <div style={{ marginBottom: "1.5rem" }}>
          <label htmlFor="password" style={{ display: "block", marginBottom: "0.5rem", fontWeight: 500 }}>
            Password
          </label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            style={{
              width: "100%",
              padding: "0.75rem",
              borderRadius: "4px",
              border: "1px solid #555",
              background: "#1a1a1a",
              color: "#e6e9f0",
              boxSizing: "border-box",
            }}
            placeholder="password"
          />
        </div>

        <div style={{ marginBottom: "2rem" }}>
          <label htmlFor="tenant" style={{ display: "block", marginBottom: "0.5rem", fontWeight: 500 }}>
            Tenant Slug
          </label>
          <input
            id="tenant"
            type="text"
            value={tenantSlug}
            onChange={(e) => setTenantSlug(e.target.value)}
            style={{
              width: "100%",
              padding: "0.75rem",
              borderRadius: "4px",
              border: "1px solid #555",
              background: "#1a1a1a",
              color: "#e6e9f0",
              boxSizing: "border-box",
            }}
            placeholder="acme"
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          style={{
            width: "100%",
            padding: "0.75rem",
            background: loading ? "#555" : "#1976d2",
            color: "white",
            border: "none",
            borderRadius: "4px",
            fontSize: "1rem",
            fontWeight: 500,
            cursor: loading ? "not-allowed" : "pointer",
          }}
        >
          {loading ? "Logging in..." : "Login"}
        </button>
      </form>

      <div style={{ marginTop: "2rem", padding: "1rem", background: "#1a1a1a", borderRadius: "8px", fontSize: "0.875rem", color: "#999" }}>
        <p style={{ margin: "0 0 0.5rem 0", fontWeight: 500 }}>Demo credentials:</p>
        <p style={{ margin: "0.25rem 0" }}>
          <strong>Admin:</strong> admin@truststack.local / change-me-local
        </p>
        <p style={{ margin: "0.25rem 0" }}>
          <strong>Analyst:</strong> analyst@truststack.local / change-me-local
        </p>
        <p style={{ margin: "0.25rem 0" }}>
          <strong>Tenant:</strong> acme
        </p>
      </div>
    </div>
  );
}
