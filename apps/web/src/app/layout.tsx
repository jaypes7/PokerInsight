import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PokerInsight",
  description: "Analise de hand histories de poker.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}
