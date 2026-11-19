import type { Metadata } from "next";
import { Toaster } from "sonner";
import "./globals.css";

export const metadata: Metadata = {
  title: "ScriptForge AI — Autonomous Text-to-Script AI Agent",
  description:
    "Intelligently convert unstructured text, logs, data, and specs into optimized, validated, and executable scripts.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="font-sans bg-background text-foreground min-h-screen antialiased selection:bg-primary/30">
        {children}
        <Toaster position="bottom-right" theme="dark" richColors closeButton />
      </body>
    </html>
  );
}
