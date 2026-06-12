"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { getAccessToken } from "../../lib/auth";
import { useRouter } from "next/navigation";

export default function DashboardPage() {
  const router = useRouter();
  const token = getAccessToken();
  const [stats, setStats] = useState({
    totalCases: 0,
    pendingReview: 0,
    approved: 0,
    rejected: 0,
  });

  useEffect(() => {
    if (!token) {
      router.push("/login");
      return;
    }
    // TODO: fetch stats from API
    setStats({ totalCases: 42, pendingReview: 5, approved: 30, rejected: 7 });
  }, [token, router]);

  return (
    <div>
      <h1 style={{ marginBottom: "2rem" }}>Analyst Dashboard</h1>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
          gap: "1.5rem",
          marginBottom: "2rem",
        }}
      >
        <div style={{ background: "#1a1a1a", padding: "1.5rem", borderRadius: "8px", border: "1px solid #333" }}>
          <div style={{ opacity: 0.7, marginBottom: "0.5rem" }}>Total Cases</div>
          <div style={{ fontSize: "2rem", fontWeight: "bold", color: "#1976d2" }}>{stats.totalCases}</div>
        </div>
        <div style={{ background: "#1a1a1a", padding: "1.5rem", borderRadius: "8px", border: "1px solid #333" }}>
          <div style={{ opacity: 0.7, marginBottom: "0.5rem" }}>Pending Review</div>
          <div style={{ fontSize: "2rem", fontWeight: "bold", color: "#f57c00" }}>{stats.pendingReview}</div>
        </div>
        <div style={{ background: "#1a1a1a", padding: "1.5rem", borderRadius: "8px", border: "1px solid #333" }}>
          <div style={{ opacity: 0.7, marginBottom: "0.5rem" }}>Approved</div>
          <div style={{ fontSize: "2rem", fontWeight: "bold", color: "#388e3c" }}>{stats.approved}</div>
        </div>
        <div style={{ background: "#1a1a1a", padding: "1.5rem", borderRadius: "8px", border: "1px solid #333" }}>
          <div style={{ opacity: 0.7, marginBottom: "0.5rem" }}>Rejected</div>
          <div style={{ fontSize: "2rem", fontWeight: "bold", color: "#d32f2f" }}>{stats.rejected}</div>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "1.5rem" }}>
        <Link
          href="/dashboard/cases"
          style={{
            display: "block",
            padding: "2rem",
            background: "#1a1a1a",
            border: "1px solid #333",
            borderRadius: "8px",
            textDecoration: "none",
            color: "inherit",
            transition: "border-color 0.2s",
            cursor: "pointer",
          }}
          onMouseEnter={(e) => (e.currentTarget.style.borderColor = "#555")}
          onMouseLeave={(e) => (e.currentTarget.style.borderColor = "#333")}
        >
          <div style={{ fontSize: "1.2rem", fontWeight: "bold", marginBottom: "0.5rem" }}>View Cases</div>
          <div style={{ opacity: 0.7 }}>Browse all onboarding cases with filters</div>
        </Link>

        <Link
          href="/dashboard/review"
          style={{
            display: "block",
            padding: "2rem",
            background: "#1a1a1a",
            border: "1px solid #333",
            borderRadius: "8px",
            textDecoration: "none",
            color: "inherit",
            transition: "border-color 0.2s",
            cursor: "pointer",
          }}
          onMouseEnter={(e) => (e.currentTarget.style.borderColor = "#555")}
          onMouseLeave={(e) => (e.currentTarget.style.borderColor = "#333")}
        >
          <div style={{ fontSize: "1.2rem", fontWeight: "bold", marginBottom: "0.5rem" }}>Review Queue</div>
          <div style={{ opacity: 0.7 }}>Manual review tasks pending approval</div>
        </Link>

        <Link
          href="/dashboard/audit"
          style={{
            display: "block",
            padding: "2rem",
            background: "#1a1a1a",
            border: "1px solid #333",
            borderRadius: "8px",
            textDecoration: "none",
            color: "inherit",
            transition: "border-color 0.2s",
            cursor: "pointer",
          }}
          onMouseEnter={(e) => (e.currentTarget.style.borderColor = "#555")}
          onMouseLeave={(e) => (e.currentTarget.style.borderColor = "#333")}
        >
          <div style={{ fontSize: "1.2rem", fontWeight: "bold", marginBottom: "0.5rem" }}>Audit Log</div>
          <div style={{ opacity: 0.7 }}>View all system events and decisions</div>
        </Link>
      </div>
    </div>
  );
}
