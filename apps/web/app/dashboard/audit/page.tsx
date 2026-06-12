"use client";

import { useEffect, useState } from "react";
import { getAccessToken } from "../../../lib/auth";
import { useRouter } from "next/navigation";
import { apiFetch } from "../../../lib/api";
import { LoadingSpinner } from "../../../components/LoadingSpinner";
import { ErrorBanner } from "../../../components/ErrorBanner";

interface AuditEvent {
  id: string;
  action: string;
  resource_type: string;
  actor_id: string;
  created_at: string;
  data?: Record<string, any>;
}

export default function AuditPage() {
  const router = useRouter();
  const token = getAccessToken();
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchAction, setSearchAction] = useState("");

  useEffect(() => {
    if (!token) {
      router.push("/login");
      return;
    }

    const loadEvents = async () => {
      try {
        const res = await apiFetch<{ items: AuditEvent[] }>("/v1/audit-events?limit=200", {
          method: "GET",
        });
        setEvents(res.items || []);
      } catch (err) {
        setError((err as any).message || "Failed to load audit events");
      } finally {
        setLoading(false);
      }
    };

    loadEvents();
  }, [token, router]);

  const filteredEvents = searchAction
    ? events.filter((e) => e.action.toLowerCase().includes(searchAction.toLowerCase()) || e.resource_type.toLowerCase().includes(searchAction.toLowerCase()))
    : events;

  return (
    <div>
      <h1 style={{ marginBottom: "1.5rem" }}>Audit Log</h1>

      {error && <ErrorBanner error={error} onDismiss={() => setError(null)} />}

      <div style={{ marginBottom: "1.5rem" }}>
        <input
          type="text"
          placeholder="Search by action or resource type..."
          value={searchAction}
          onChange={(e) => setSearchAction(e.target.value)}
          style={{
            width: "100%",
            padding: "0.75rem",
            borderRadius: "4px",
            border: "1px solid #555",
            background: "#1a1a1a",
            color: "#e6e9f0",
            boxSizing: "border-box",
          }}
        />
      </div>

      {loading && <LoadingSpinner message="Loading audit events..." />}

      {!loading && filteredEvents.length === 0 && (
        <div style={{ padding: "2rem", textAlign: "center", opacity: 0.6 }}>
          No audit events found.
        </div>
      )}

      {!loading && filteredEvents.length > 0 && (
        <div
          style={{
            overflowX: "auto",
            borderRadius: "8px",
            border: "1px solid #333",
            background: "#1a1a1a",
          }}
        >
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.875rem" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid #333" }}>
                <th style={{ padding: "1rem", textAlign: "left", opacity: 0.7 }}>Timestamp</th>
                <th style={{ padding: "1rem", textAlign: "left", opacity: 0.7 }}>Action</th>
                <th style={{ padding: "1rem", textAlign: "left", opacity: 0.7 }}>Resource Type</th>
                <th style={{ padding: "1rem", textAlign: "left", opacity: 0.7 }}>Actor</th>
              </tr>
            </thead>
            <tbody>
              {filteredEvents.map((event) => (
                <tr key={event.id} style={{ borderBottom: "1px solid #2a2a2a" }}>
                  <td style={{ padding: "1rem" }}>
                    {new Date(event.created_at).toLocaleString()}
                  </td>
                  <td style={{ padding: "1rem" }}>
                    <code style={{ background: "#0b1020", padding: "0.25rem 0.5rem", borderRadius: "4px" }}>{event.action}</code>
                  </td>
                  <td style={{ padding: "1rem" }}>{event.resource_type}</td>
                  <td style={{ padding: "1rem", opacity: 0.7 }}>{event.actor_id}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
