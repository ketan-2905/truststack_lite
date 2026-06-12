"use client";

export function LoadingSpinner({ message = "Loading..." }: { message?: string }) {
  return (
    <div style={{ textAlign: "center", padding: "2rem", opacity: 0.6 }}>
      <div style={{ fontSize: "1rem", marginBottom: "1rem" }}>{message}</div>
    </div>
  );
}
