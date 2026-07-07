import type { Metadata } from "next";
import { Cormorant_Garamond, Outfit, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const serif = Cormorant_Garamond({
  weight: ["400", "500", "600"],
  style: ["normal", "italic"],
  subsets: ["latin"],
  variable: "--nf-serif",
  display: "swap",
});

const sans = Outfit({
  subsets: ["latin"],
  variable: "--nf-sans",
  display: "swap",
});

const mono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--nf-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "InterviewForge — AI Mock Interviews",
  description: "Adaptive AI interview coach with real-time evaluation",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${serif.variable} ${sans.variable} ${mono.variable}`}>
      <body className="bg-surface text-text font-sans antialiased min-h-screen">
        {children}
      </body>
    </html>
  );
}
