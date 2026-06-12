"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { createApplicant, createCase } from "../../../lib/api";
import { getAccessToken } from "../../../lib/auth";
import { ErrorBanner } from "../../../components/ErrorBanner";
import { useEffect } from "react";

export default function ApplicantStartPage() {
  const router = useRouter();
  const token = getAccessToken();
  const [email, setEmail] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!token) {
      router.push("/login");
    }
  }, [token, router]);

  async function handleStart(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const applicant = await createApplicant(email);
      const caseRes = await createCase(applicant.id);
      router.push(`/applicant/case/${caseRes.id}`);
    } catch (err) {
      setError((err as any).message || "Failed to start case");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ maxWidth: "600px", margin: "2rem auto" }}>
      <h1 style={{ marginBottom: "2rem" }}>Start Onboarding</h1>

      {error && <ErrorBanner error={error} onDismiss={() => setError(null)} />}

      <div style={{ background: "#1a1a1a", padding: "2rem", borderRadius: "8px", border: "1px solid #333" }}>
        <form onSubmit={handleStart}>
          <div style={{ marginBottom: "1.5rem" }}>
            <label htmlFor="email" style={{ display: "block", marginBottom: "0.5rem", fontWeight: 500 }}>
              Applicant Email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              disabled={loading}
              style={{
                width: "100%",
                padding: "0.75rem",
                borderRadius: "4px",
                border: "1px solid #555",
                background: "#0b1020",
                color: "#e6e9f0",
                boxSizing: "border-box",
                opacity: loading ? 0.5 : 1,
              }}
              placeholder="applicant@example.com"
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
            {loading ? "Starting..." : "Start Case"}
          </button>
        </form>
      </div>
    </div>
  );
}
