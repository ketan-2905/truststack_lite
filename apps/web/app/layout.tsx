import type { ReactNode } from "react";

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
        {children}
      </body>
    </html>
  );
}
