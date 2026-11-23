"use client";

import { useEffect, useState } from "react";
import { apiRequest } from "@/lib/api-client";

export default function HomePage() {
  const [isOnline, setIsOnline] = useState<boolean | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function checkHealth() {
      try {
        const res = await apiRequest<{ status: string }>("/health");
        if (isMounted) {
          setIsOnline(res.code === 200 && res.data?.status === "healthy");
        }
      } catch (err) {
        if (isMounted) {
          setIsOnline(false);
        }
      }
    }

    checkHealth();
    const interval = setInterval(checkHealth, 10000); // Check every 10s

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  return (
    <main className="relative flex min-h-screen flex-col items-center justify-center p-8 text-center bg-slate-50">
      <h1 className="text-4xl font-extrabold tracking-tight text-slate-900">
        TRACK - EOS Management System
      </h1>

      {/* Bottom right online status indicator */}
      <div className="fixed bottom-6 right-6 flex items-center gap-2 rounded-full border border-slate-200 bg-white px-4 py-2 shadow-sm text-sm font-medium">
        {isOnline === null ? (
          <>
            <span className="h-2.5 w-2.5 rounded-full bg-amber-400 animate-pulse" />
            <span className="text-slate-600">Checking...</span>
          </>
        ) : isOnline ? (
          <>
            <span className="h-2.5 w-2.5 rounded-full bg-emerald-500" />
            <span className="text-emerald-700">Online</span>
          </>
        ) : (
          <>
            <span className="h-2.5 w-2.5 rounded-full bg-rose-500" />
            <span className="text-rose-700">Offline</span>
          </>
        )}
      </div>
    </main>
  );
}
