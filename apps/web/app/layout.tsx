import type { ReactNode } from "react";
import { NavBar } from "../components/NavBar";

export const metadata = {
  title: "TrustStack Lite",
  description: "Risk-adaptive onboarding and consent governance",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body
        style={{
          fontFamily: "system-ui, sans-serif",
          margin: 0,
          background: "#0b1020",
          color: "#e6e9f0",
        }}
      >
        <NavBar />
        <main style={{ maxWidth: "1200px", margin: "0 auto", padding: "2rem 1.5rem" }}>{children}</main>
      </body>
    </html>
  );
}
