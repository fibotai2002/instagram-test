"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import Sidebar from "@/components/Sidebar";

export default function ClientLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
    const token = localStorage.getItem("admin_token");
    if (!token && pathname !== "/login") {
      router.push("/login");
    } else if (token && pathname === "/login") {
      router.push("/");
    }
  }, [pathname, router]);

  if (!isClient) return null; // Prevent hydration mismatch
  
  const isLoginPage = pathname === "/login";

  return (
    <>
      {!isLoginPage && <Sidebar />}
      <main className={`flex-1 overflow-y-auto ${isLoginPage ? '' : 'p-8'}`}>
        {children}
      </main>
    </>
  );
}
