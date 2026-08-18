import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ApplyAI",
  description: "Analyze job applications against resume evidence.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
