import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CalibraytAI — Construction Intelligence. Calibrated.",
  description: "CalibraytAI connects the complete construction lifecycle through one authoritative project record.",
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
