"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { getUserRole, clearTokens, getAccessToken } from "../lib/auth";
import { logout } from "../lib/api";

export function NavBar() {
  const [role, setRole] = useState<string | null>(null);
  const router = useRouter();
  const token = getAccessToken();

  useEffect(() => {
    if (token) {
      setRole(getUserRole());
    }
  }, [token]);

  async function handleLogout() {
    await logout();
    router.push("/login");
  }

  if (!token) return null;

  return (
    <nav
      style={{
        background: "#1a1a1a",
        color: "white",
        padding: "1rem 1.5rem",
        borderBottom: "1px solid #333",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
      }}
    >
      <div style={{ display: "flex", gap: "2rem", alignItems: "center" }}>
        <Link href="/" style={{ fontWeight: "bold", fontSize: "1.1rem", textDecoration: "none", color: "white" }}>
          TrustStack Lite
        </Link>
        <div style={{ display: "flex", gap: "1rem" }}>
          {role === "analyst" && (
            <>
              <Link href="/dashboard" style={{ textDecoration: "none", color: "#aaa" }}>
                Dashboard
              </Link>
              <Link href="/dashboard/cases" style={{ textDecoration: "none", color: "#aaa" }}>
                Cases
              </Link>
              <Link href="/dashboard/review" style={{ textDecoration: "none", color: "#aaa" }}>
                Review Queue
              </Link>
              <Link href="/dashboard/audit" style={{ textDecoration: "none", color: "#aaa" }}>
                Audit
              </Link>
            </>
          )}
          {role === "applicant" && (
            <>
              <Link href="/applicant/start" style={{ textDecoration: "none", color: "#aaa" }}>
                Start Case
              </Link>
            </>
          )}
        </div>
      </div>
      <button
        onClick={handleLogout}
        style={{
          padding: "0.5rem 1rem",
          background: "#333",
          color: "white",
          border: "1px solid #555",
          borderRadius: "4px",
          cursor: "pointer",
        }}
      >
        Logout
      </button>
    </nav>
  );
}
