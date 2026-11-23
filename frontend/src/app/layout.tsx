import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Track - EOS Management System",
  description: "Leadership weekly meeting, rocks, measurables, issues and to-dos",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-50 text-slate-900">{children}</body>
    </html>
  );
}
