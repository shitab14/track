"use client";

import { useEffect, useState } from "react";
import { apiRequest } from "@/lib/api-client";

interface HealthData {
  status: string;
  backend: string;
  database: string;
  project: string;
  app_now: string;
  timezone: string;
}

export default function HomePage() {
  const [backendStatus, setBackendStatus] = useState<"checking" | "online" | "offline">("checking");
  const [dbStatus, setDbStatus] = useState<"checking" | "online" | "offline">("checking");

  useEffect(() => {
    let isMounted = true;

    async function checkHealth() {
      try {
        const res = await apiRequest<HealthData>("/health");
        if (isMounted) {
          if (res.data) {
            setBackendStatus(res.data.backend === "healthy" ? "online" : "offline");
            setDbStatus(res.data.database === "healthy" ? "online" : "offline");
          } else {
            setBackendStatus("offline");
            setDbStatus("offline");
          }
        }
      } catch (err) {
        if (isMounted) {
          setBackendStatus("offline");
          setDbStatus("offline");
        }
      }
    }

    checkHealth();
    const interval = setInterval(checkHealth, 5000); // Check every 5s

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

      {/* Bottom right detailed status indicator */}
      <div className="fixed bottom-4 right-4 flex items-center gap-3 rounded-lg border border-slate-200 bg-white px-3 py-1.5 shadow-sm text-xs text-slate-600 font-medium">
        {/* Backend Indicator */}
        <div className="flex items-center gap-1.5">
          <span className="text-slate-500">Backend:</span>
          {backendStatus === "checking" ? (
            <span className="inline-flex items-center gap-1 text-amber-600">
              <span className="h-2 w-2 rounded-full bg-amber-400 animate-pulse" />
              <span>checking</span>
            </span>
          ) : backendStatus === "online" ? (
            <span className="inline-flex items-center gap-1 text-emerald-700">
              <span className="h-2 w-2 rounded-full bg-emerald-500" />
              <span>online</span>
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 text-rose-700">
              <span className="h-2 w-2 rounded-full bg-rose-500" />
              <span>offline</span>
            </span>
          )}
        </div>

        <span className="text-slate-300">|</span>

        {/* Database Indicator */}
        <div className="flex items-center gap-1.5">
          <span className="text-slate-500">DB:</span>
          {dbStatus === "checking" ? (
            <span className="inline-flex items-center gap-1 text-amber-600">
              <span className="h-2 w-2 rounded-full bg-amber-400 animate-pulse" />
              <span>checking</span>
            </span>
          ) : dbStatus === "online" ? (
            <span className="inline-flex items-center gap-1 text-emerald-700">
              <span className="h-2 w-2 rounded-full bg-emerald-500" />
              <span>online</span>
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 text-rose-700">
              <span className="h-2 w-2 rounded-full bg-rose-500" />
              <span>offline</span>
            </span>
          )}
        </div>
      </div>
    </main>
  );
}
