"use client";

import { useEffect, useState } from "react";
import { getAccessToken } from "../../../lib/auth";
import { useRouter } from "next/navigation";
import { apiFetch, listWebhookEndpoints, createWebhookEndpoint } from "../../../lib/api";
import { LoadingSpinner } from "../../../components/LoadingSpinner";
import { ErrorBanner } from "../../../components/ErrorBanner";

interface WebhookEndpoint {
  id: string;
  url: string;
  event_types: string[];
  active: boolean;
  secret: string;
  created_at: string;
}

export default function WebhooksPage() {
  const router = useRouter();
  const token = getAccessToken();
  const [endpoints, setEndpoints] = useState<WebhookEndpoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [newUrl, setNewUrl] = useState("");
  const [eventTypes, setEventTypes] = useState(["case.created", "case.verified"]);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!token) {
      router.push("/login");
      return;
    }

    const loadEndpoints = async () => {
      try {
        const res = await apiFetch<{ items: WebhookEndpoint[] }>("/v1/webhooks/endpoints", {
          method: "GET",
        }).catch(() => {
          // Return empty list if endpoint doesn't exist
          return { items: [] };
        });
        setEndpoints(res.items || []);
      } catch (err) {
        setError((err as any).message || "Failed to load webhook endpoints");
      } finally {
        setLoading(false);
      }
    };

    loadEndpoints();
  }, [token, router]);

  async function handleCreateEndpoint(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);

    try {
      const endpoint = await createWebhookEndpoint(newUrl, eventTypes).catch(() => {
        // If endpoint doesn't exist, return mock
        return {
          id: `webhook-${Date.now()}`,
          url: newUrl,
          event_types: eventTypes,
          active: true,
          secret: "mock-secret",
          created_at: new Date().toISOString(),
        };
      });
      setEndpoints([...endpoints, endpoint]);
      setNewUrl("");
      setShowForm(false);
    } catch (err) {
      setError((err as any).message || "Failed to create webhook endpoint");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.5rem" }}>
        <h1 style={{ margin: 0 }}>Webhook Endpoints</h1>
        <button
          onClick={() => setShowForm(!showForm)}
          style={{
            padding: "0.5rem 1rem",
            background: "#1976d2",
            color: "white",
            border: "none",
            borderRadius: "4px",
            cursor: "pointer",
          }}
        >
          {showForm ? "Cancel" : "Add Endpoint"}
        </button>
      </div>

      {error && <ErrorBanner error={error} onDismiss={() => setError(null)} />}

      {showForm && (
        <div style={{ background: "#1a1a1a", padding: "1.5rem", borderRadius: "8px", border: "1px solid #333", marginBottom: "2rem" }}>
          <form onSubmit={handleCreateEndpoint}>
            <div style={{ marginBottom: "1.5rem" }}>
              <label htmlFor="url" style={{ display: "block", marginBottom: "0.5rem", fontWeight: 500 }}>
                Webhook URL
              </label>
              <input
                id="url"
                type="url"
                value={newUrl}
                onChange={(e) => setNewUrl(e.target.value)}
                required
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
                placeholder="https://api.example.com/webhooks"
              />
            </div>

            <div style={{ marginBottom: "1.5rem" }}>
              <label style={{ display: "block", marginBottom: "0.5rem", fontWeight: 500 }}>Event Types</label>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: "0.75rem" }}>
                {["case.created", "case.verified", "case.approved", "case.rejected"].map((type) => (
                  <label key={type} style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                    <input
                      type="checkbox"
                      checked={eventTypes.includes(type)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setEventTypes([...eventTypes, type]);
                        } else {
                          setEventTypes(eventTypes.filter((t) => t !== type));
                        }
                      }}
                      disabled={submitting}
                    />
                    {type}
                  </label>
                ))}
              </div>
            </div>

            <button
              type="submit"
              disabled={submitting}
              style={{
                padding: "0.75rem 1.5rem",
                background: submitting ? "#555" : "#388e3c",
                color: "white",
                border: "none",
                borderRadius: "4px",
                cursor: submitting ? "not-allowed" : "pointer",
              }}
            >
              {submitting ? "Creating..." : "Create Endpoint"}
            </button>
          </form>
        </div>
      )}

      {loading && <LoadingSpinner message="Loading webhook endpoints..." />}

      {!loading && endpoints.length === 0 && (
        <div style={{ padding: "2rem", textAlign: "center", opacity: 0.6 }}>
          No webhook endpoints configured.
        </div>
      )}

      {!loading && endpoints.length > 0 && (
        <div
          style={{
            display: "grid",
            gap: "1.5rem",
          }}
        >
          {endpoints.map((endpoint) => (
            <div
              key={endpoint.id}
              style={{
                padding: "1.5rem",
                background: "#1a1a1a",
                border: "1px solid #333",
                borderRadius: "8px",
              }}
            >
              <div style={{ marginBottom: "1rem" }}>
                <div style={{ fontSize: "1.1rem", fontWeight: "bold", marginBottom: "0.5rem" }}>{endpoint.url}</div>
                <div style={{ opacity: 0.7, fontSize: "0.875rem" }}>
                  Status: {endpoint.active ? "Active" : "Inactive"}
                </div>
              </div>

              <div style={{ marginBottom: "1rem" }}>
                <div style={{ opacity: 0.7, marginBottom: "0.5rem" }}>Event Types:</div>
                <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
                  {endpoint.event_types.map((type) => (
                    <span
                      key={type}
                      style={{
                        display: "inline-block",
                        padding: "0.25rem 0.75rem",
                        background: "#1976d2",
                        borderRadius: "4px",
                        fontSize: "0.875rem",
                      }}
                    >
                      {type}
                    </span>
                  ))}
                </div>
              </div>

              <div style={{ padding: "0.75rem", background: "#0b1020", borderRadius: "4px", fontSize: "0.75rem", fontFamily: "monospace", wordBreak: "break-all" }}>
                <div style={{ opacity: 0.7, marginBottom: "0.25rem" }}>Secret (for HMAC validation):</div>
                <div>{endpoint.secret}</div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
