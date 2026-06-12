"use client";

const statusColors: Record<string, { bg: string; fg: string }> = {
  approved: { bg: "#e8f5e9", fg: "#2e7d32" },
  pending: { bg: "#fff3e0", fg: "#e65100" },
  rejected: { bg: "#ffebee", fg: "#c62828" },
  manual_review: { bg: "#e3f2fd", fg: "#1565c0" },
  submitted: { bg: "#f3e5f5", fg: "#6a1b9a" },
  failed: { bg: "#ffebee", fg: "#c62828" },
};

export function StatusBadge({ status }: { status: string }) {
  const colors = statusColors[status.toLowerCase()] || { bg: "#f5f5f5", fg: "#424242" };
  return (
    <span
      style={{
        display: "inline-block",
        padding: "0.5rem 1rem",
        borderRadius: "16px",
        fontSize: "0.875rem",
        fontWeight: 500,
        background: colors.bg,
        color: colors.fg,
      }}
    >
      {status}
    </span>
  );
}
