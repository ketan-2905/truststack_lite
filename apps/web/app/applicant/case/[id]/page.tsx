"use client";

import { useEffect, useState } from "react";
import { getAccessToken } from "../../../../lib/auth";
import { useRouter, useParams } from "next/navigation";
import { apiFetch, getCase, uploadDocument } from "../../../../lib/api";
import { LoadingSpinner } from "../../../../components/LoadingSpinner";
import { ErrorBanner } from "../../../../components/ErrorBanner";
import { StatusBadge } from "../../../../components/StatusBadge";

interface Case {
  id: string;
  applicant_id: string;
  state: string;
  risk_score: number | null;
  risk_severity: string | null;
  created_at: string;
}

export default function CaseDetailPage() {
  const router = useRouter();
  const params = useParams();
  const caseId = params.id as string;
  const token = getAccessToken();
  const [caseData, setCaseData] = useState<Case | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    if (!token) {
      router.push("/login");
      return;
    }

    const loadCase = async () => {
      try {
        const res = await getCase(caseId);
        setCaseData(res);
      } catch (err) {
        setError((err as any).message || "Failed to load case");
      } finally {
        setLoading(false);
      }
    };

    loadCase();
  }, [token, router, caseId]);

  async function handleFileUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    try {
      await uploadDocument(caseId, file);
      // Reload case
      const res = await getCase(caseId);
      setCaseData(res);
    } catch (err) {
      setError((err as any).message || "Failed to upload document");
    } finally {
      setUploading(false);
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

      {loading && <LoadingSpinner message="Loading case..." />}

      {!loading && caseData && (
        <div>
          <h1 style={{ marginBottom: "2rem" }}>Case {caseData.id.substring(0, 8)}</h1>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))", gap: "1.5rem", marginBottom: "2rem" }}>
            <div style={{ background: "#1a1a1a", padding: "1.5rem", borderRadius: "8px", border: "1px solid #333" }}>
              <div style={{ opacity: 0.7, marginBottom: "0.5rem" }}>Status</div>
              <StatusBadge status={caseData.state} />
            </div>

            {caseData.risk_severity && (
              <div style={{ background: "#1a1a1a", padding: "1.5rem", borderRadius: "8px", border: "1px solid #333" }}>
                <div style={{ opacity: 0.7, marginBottom: "0.5rem" }}>Risk Severity</div>
                <div>{caseData.risk_severity}</div>
              </div>
            )}

            {caseData.risk_score !== null && (
              <div style={{ background: "#1a1a1a", padding: "1.5rem", borderRadius: "8px", border: "1px solid #333" }}>
                <div style={{ opacity: 0.7, marginBottom: "0.5rem" }}>Risk Score</div>
                <div style={{ fontSize: "1.5rem", fontWeight: "bold" }}>{caseData.risk_score.toFixed(1)}</div>
              </div>
            )}
          </div>

          <div style={{ background: "#1a1a1a", padding: "2rem", borderRadius: "8px", border: "1px solid #333" }}>
            <h2 style={{ fontSize: "1.1rem", marginBottom: "1.5rem" }}>Document Upload</h2>

            <div style={{ marginBottom: "1rem" }}>
              <label htmlFor="file" style={{ display: "block", marginBottom: "0.5rem", fontWeight: 500 }}>
                Upload Identity Document
              </label>
              <input
                id="file"
                type="file"
                onChange={handleFileUpload}
                disabled={uploading}
                accept="image/*,.pdf"
                style={{
                  display: "block",
                  padding: "0.5rem",
                  opacity: uploading ? 0.5 : 1,
                }}
              />
            </div>

            {uploading && <LoadingSpinner message="Uploading..." />}
          </div>
        </div>
      )}
    </div>
  );
}
