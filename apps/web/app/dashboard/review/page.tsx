"use client";

import { useEffect, useState } from "react";
import { getAccessToken } from "../../../lib/auth";
import { useRouter } from "next/navigation";
import { apiFetch } from "../../../lib/api";
import { LoadingSpinner } from "../../../components/LoadingSpinner";
import { ErrorBanner } from "../../../components/ErrorBanner";
import { StatusBadge } from "../../../components/StatusBadge";

interface ReviewTask {
  id: string;
  case_id: string;
  status: string;
  created_at: string;
}

export default function ReviewQueuePage() {
  const router = useRouter();
  const token = getAccessToken();
  const [tasks, setTasks] = useState<ReviewTask[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      router.push("/login");
      return;
    }

    const loadTasks = async () => {
      try {
        // Try to fetch from /v1/review/tasks endpoint if it exists
        const res = await apiFetch<{ items: ReviewTask[] }>("/v1/review/tasks?status=pending&limit=100", {
          method: "GET",
        }).catch(() => {
          // Fallback: return empty list if endpoint doesn't exist yet
          return { items: [] };
        });
        setTasks(res.items || []);
      } catch (err) {
        setError((err as any).message || "Failed to load review tasks");
      } finally {
        setLoading(false);
      }
    };

    loadTasks();
  }, [token, router]);

  return (
    <div>
      <h1 style={{ marginBottom: "1.5rem" }}>Review Queue</h1>

      {error && <ErrorBanner error={error} onDismiss={() => setError(null)} />}

      {loading && <LoadingSpinner message="Loading review tasks..." />}

      {!loading && tasks.length === 0 && (
        <div style={{ padding: "2rem", textAlign: "center", opacity: 0.6 }}>
          No pending review tasks.
        </div>
      )}

      {!loading && tasks.length > 0 && (
        <div
          style={{
            display: "grid",
            gap: "1.5rem",
          }}
        >
          {tasks.map((task) => (
            <div
              key={task.id}
              onClick={() => router.push(`/dashboard/review/${task.id}`)}
              style={{
                padding: "1.5rem",
                background: "#1a1a1a",
                border: "1px solid #333",
                borderRadius: "8px",
                cursor: "pointer",
                transition: "border-color 0.2s",
              }}
              onMouseEnter={(e) => (e.currentTarget.style.borderColor = "#555")}
              onMouseLeave={(e) => (e.currentTarget.style.borderColor = "#333")}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start" }}>
                <div>
                  <div style={{ fontSize: "1.1rem", fontWeight: "bold", marginBottom: "0.5rem" }}>
                    Case {task.case_id.substring(0, 8)}
                  </div>
                  <div style={{ opacity: 0.7, fontSize: "0.875rem" }}>
                    Task ID: {task.id.substring(0, 8)}
                  </div>
                </div>
                <StatusBadge status={task.status} />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
