"use client";

import { useEffect, useState } from "react";
import { getAccessToken } from "../../../lib/auth";
import { useRouter } from "next/navigation";
import { apiFetch } from "../../../lib/api";
import { LoadingSpinner } from "../../../components/LoadingSpinner";
import { ErrorBanner } from "../../../components/ErrorBanner";
import { StatusBadge } from "../../../components/StatusBadge";

interface Case {
  id: string;
  applicant_id: string;
  reference: string | null;
  state: string;
  risk_score: number | null;
  risk_severity: string | null;
  created_at: string;
}

export default function CasesPage() {
  const router = useRouter();
  const token = getAccessToken();
  const [cases, setCases] = useState<Case[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState("all");

  useEffect(() => {
    if (!token) {
      router.push("/login");
      return;
    }

    const loadCases = async () => {
      try {
        const res = await apiFetch<{ items: Case[] }>("/v1/onboarding-cases?limit=100", {
          method: "GET",
        });
        setCases(res.items || []);
      } catch (err) {
        setError((err as any).message || "Failed to load cases");
      } finally {
        setLoading(false);
      }
    };

    loadCases();
  }, [token, router]);

  const filteredCases = filter === "all" ? cases : cases.filter((c) => c.state.toLowerCase() === filter.toLowerCase());

  return (
    <div>
      <h1 style={{ marginBottom: "1.5rem" }}>Onboarding Cases</h1>

      {error && <ErrorBanner error={error} onDismiss={() => setError(null)} />}

      <div style={{ marginBottom: "1.5rem", display: "flex", gap: "1rem" }}>
        {["all", "submitted", "pending", "approved", "rejected"].map((status) => (
          <button
            key={status}
            onClick={() => setFilter(status)}
            style={{
              padding: "0.5rem 1rem",
              background: filter === status ? "#1976d2" : "#1a1a1a",
              color: "white",
              border: `1px solid ${filter === status ? "#1976d2" : "#333"}`,
              borderRadius: "4px",
              cursor: "pointer",
              textTransform: "capitalize",
            }}
          >
            {status}
          </button>
        ))}
      </div>

      {loading && <LoadingSpinner message="Loading cases..." />}

      {!loading && filteredCases.length === 0 && (
        <div style={{ padding: "2rem", textAlign: "center", opacity: 0.6 }}>
          No cases found.
        </div>
      )}

      {!loading && filteredCases.length > 0 && (
        <div
          style={{
            overflowX: "auto",
            borderRadius: "8px",
            border: "1px solid #333",
            background: "#1a1a1a",
          }}
        >
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid #333" }}>
                <th style={{ padding: "1rem", textAlign: "left", opacity: 0.7 }}>Reference</th>
                <th style={{ padding: "1rem", textAlign: "left", opacity: 0.7 }}>Status</th>
                <th style={{ padding: "1rem", textAlign: "left", opacity: 0.7 }}>Risk Severity</th>
                <th style={{ padding: "1rem", textAlign: "left", opacity: 0.7 }}>Risk Score</th>
                <th style={{ padding: "1rem", textAlign: "left", opacity: 0.7 }}>Created</th>
              </tr>
            </thead>
            <tbody>
              {filteredCases.map((cse) => (
                <tr
                  key={cse.id}
                  onClick={() => router.push(`/dashboard/review/${cse.id}`)}
                  style={{
                    borderBottom: "1px solid #2a2a2a",
                    cursor: "pointer",
                    transition: "background-color 0.2s",
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "#242424")}
                  onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "transparent")}
                >
                  <td style={{ padding: "1rem" }}>{cse.reference || cse.id.substring(0, 8)}</td>
                  <td style={{ padding: "1rem" }}>
                    <StatusBadge status={cse.state} />
                  </td>
                  <td style={{ padding: "1rem" }}>
                    {cse.risk_severity ? <div>{cse.risk_severity}</div> : <span style={{ opacity: 0.5 }}>—</span>}
                  </td>
                  <td style={{ padding: "1rem" }}>
                    {cse.risk_score !== null ? cse.risk_score.toFixed(1) : <span style={{ opacity: 0.5 }}>—</span>}
                  </td>
                  <td style={{ padding: "1rem", opacity: 0.7, fontSize: "0.875rem" }}>
                    {new Date(cse.created_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
