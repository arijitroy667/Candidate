import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Candidex | Hiring intelligence",
  description: "Human-led hiring workflows with explainable AI screening.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
