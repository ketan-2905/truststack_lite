"use client";

export function ErrorBanner({ error, onDismiss }: { error: string; onDismiss?: () => void }) {
  return (
    <div
      style={{
        padding: "1rem",
        marginBottom: "1rem",
        background: "#ffebee",
        border: "1px solid #ef5350",
        borderRadius: "8px",
        color: "#c62828",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span>{error}</span>
        {onDismiss && (
          <button onClick={onDismiss} style={{ background: "none", border: "none", cursor: "pointer", fontSize: "1.2rem" }}>
            ×
          </button>
        )}
      </div>
    </div>
  );
}
