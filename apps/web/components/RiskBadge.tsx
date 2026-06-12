"use client";

const riskColors: Record<string, { bg: string; fg: string }> = {
  low: { bg: "#e8f5e9", fg: "#2e7d32" },
  medium: { bg: "#fff3e0", fg: "#e65100" },
  high: { bg: "#ffebee", fg: "#c62828" },
};

export function RiskBadge({ severity }: { severity: string }) {
  const colors = riskColors[severity.toLowerCase()] || { bg: "#f5f5f5", fg: "#424242" };
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
      {severity}
    </span>
  );
}
