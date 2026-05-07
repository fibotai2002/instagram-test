import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Arzonchi Admin",
  description: "Arzonchi AI Chat boshqaruv paneli",
};

import ClientLayout from "./ClientLayout";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="uz" className="dark">
      <body className={`${geistSans.variable} ${geistMono.variable} antialiased bg-[#050505] text-zinc-100 flex h-screen overflow-hidden`}>
        <ClientLayout>{children}</ClientLayout>
      </body>
    </html>
  );
}
