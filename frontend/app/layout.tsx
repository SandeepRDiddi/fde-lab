import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "FDE Lab",
  description: "Student and instructor workspace for FDE Lab scenarios",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
