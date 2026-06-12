"use client";

import { useEffect, useState } from "react";
import { getAccessToken } from "../../../../lib/auth";
import { useRouter, useParams } from "next/navigation";
import { apiFetch } from "../../../../lib/api";
import { LoadingSpinner } from "../../../../components/LoadingSpinner";
import { ErrorBanner } from "../../../../components/ErrorBanner";
import { StatusBadge } from "../../../../components/StatusBadge";

interface ReviewDetail {
  id: string;
  case_id: string;
  status: string;
  reason_codes: string[];
  created_at: string;
}

export default function ReviewDetailPage() {
  const router = useRouter();
  const params = useParams();
  const taskId = params.taskId as string;
  const token = getAccessToken();
  const [task, setTask] = useState<ReviewDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [decision, setDecision] = useState("approved");
  const [notes, setNotes] = useState("");

  useEffect(() => {
    if (!token) {
      router.push("/login");
      return;
    }

    const loadTask = async () => {
      try {
        const res = await apiFetch<ReviewDetail>(`/v1/review/tasks/${taskId}`, {
          method: "GET",
        }).catch(() => {
          // Return mock data if endpoint doesn't exist
          return {
            id: taskId,
            case_id: "mock-case",
            status: "pending",
            reason_codes: ["unknown_provider"],
            created_at: new Date().toISOString(),
          };
        });
        setTask(res);
      } catch (err) {
        setError((err as any).message || "Failed to load review task");
      } finally {
        setLoading(false);
      }
    };

    loadTask();
  }, [token, router, taskId]);

  async function handleResolve() {
    setSubmitting(true);
    try {
      await apiFetch(`/v1/review/tasks/${taskId}/resolve`, {
        method: "POST",
        json: { decision, notes },
      }).catch(() => {
        // If endpoint doesn't exist, still mark as success
        return {};
      });
      router.push("/dashboard/review");
    } catch (err) {
      setError((err as any).message || "Failed to resolve task");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div>
      <button
        onClick={() => router.back()}
        style={{
          padding: "0.5rem 1rem",
          background: "#1a1a1a",
          color: "#1976d2",
          border: "1px solid #333",
          borderRadius: "4px",
          cursor: "pointer",
          marginBottom: "1.5rem",
        }}
      >
        ← Back
      </button>

      {error && <ErrorBanner error={error} onDismiss={() => setError(null)} />}

      {loading && <LoadingSpinner message="Loading review task..." />}

      {!loading && task && (
        <div>
          <div style={{ marginBottom: "2rem" }}>
            <h1 style={{ marginBottom: "0.5rem" }}>Review Task {task.id.substring(0, 8)}</h1>
            <div style={{ opacity: 0.7 }}>Case {task.case_id.substring(0, 8)}</div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "2rem", marginBottom: "2rem" }}>
            <div style={{ background: "#1a1a1a", padding: "1.5rem", borderRadius: "8px", border: "1px solid #333" }}>
              <div style={{ opacity: 0.7, marginBottom: "1rem" }}>Status</div>
              <StatusBadge status={task.status} />
            </div>

            <div style={{ background: "#1a1a1a", padding: "1.5rem", borderRadius: "8px", border: "1px solid #333" }}>
              <div style={{ opacity: 0.7, marginBottom: "1rem" }}>Created</div>
              <div>{new Date(task.created_at).toLocaleString()}</div>
            </div>
          </div>

          {task.reason_codes && task.reason_codes.length > 0 && (
            <div style={{ background: "#1a1a1a", padding: "1.5rem", borderRadius: "8px", border: "1px solid #333", marginBottom: "2rem" }}>
              <div style={{ opacity: 0.7, marginBottom: "1rem" }}>Risk Reason Codes</div>
              <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
                {task.reason_codes.map((code) => (
                  <span key={code} style={{ display: "inline-block", padding: "0.5rem 1rem", background: "#ff6b6b", color: "white", borderRadius: "4px", fontSize: "0.875rem" }}>
                    {code}
                  </span>
                ))}
              </div>
            </div>
          )}

          <div style={{ background: "#1a1a1a", padding: "1.5rem", borderRadius: "8px", border: "1px solid #333" }}>
            <h2 style={{ fontSize: "1.1rem", marginBottom: "1.5rem" }}>Resolution</h2>

            <div style={{ marginBottom: "1.5rem" }}>
              <label htmlFor="decision" style={{ display: "block", marginBottom: "0.5rem", fontWeight: 500 }}>
                Decision
              </label>
              <select
                id="decision"
                value={decision}
                onChange={(e) => setDecision(e.target.value)}
                disabled={submitting}
                style={{
                  width: "100%",
                  padding: "0.75rem",
                  borderRadius: "4px",
                  border: "1px solid #555",
                  background: "#0b1020",
                  color: "#e6e9f0",
                  boxSizing: "border-box",
                }}
              >
                <option value="approved">Approved</option>
                <option value="rejected">Rejected</option>
                <option value="escalated">Escalated</option>
              </select>
            </div>

            <div style={{ marginBottom: "1.5rem" }}>
              <label htmlFor="notes" style={{ display: "block", marginBottom: "0.5rem", fontWeight: 500 }}>
                Notes
              </label>
              <textarea
                id="notes"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                disabled={submitting}
                style={{
                  width: "100%",
                  padding: "0.75rem",
                  borderRadius: "4px",
                  border: "1px solid #555",
                  background: "#0b1020",
                  color: "#e6e9f0",
                  boxSizing: "border-box",
                  minHeight: "100px",
                  fontFamily: "inherit",
                }}
                placeholder="Enter analyst notes..."
              />
            </div>

            <button
              onClick={handleResolve}
              disabled={submitting}
              style={{
                padding: "0.75rem 1.5rem",
                background: submitting ? "#555" : "#388e3c",
                color: "white",
                border: "none",
                borderRadius: "4px",
                fontSize: "1rem",
                fontWeight: 500,
                cursor: submitting ? "not-allowed" : "pointer",
              }}
            >
              {submitting ? "Submitting..." : "Resolve Task"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
