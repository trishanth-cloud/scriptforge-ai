"use client";

import { useEffect, useState } from "react";
import { Zap, Github, Circle } from "lucide-react";
import * as api from "@/lib/api";

export default function Header() {
  const [healthy, setHealthy] = useState<boolean | null>(null);

  useEffect(() => {
    let mounted = true;
    const check = async () => {
      try {
        await api.healthCheck();
        if (mounted) setHealthy(true);
      } catch {
        if (mounted) setHealthy(false);
      }
    };
    check();
    const interval = setInterval(check, 30000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  return (
    <header className="bg-surface border-b border-surface-border px-6 py-3 flex items-center justify-between shrink-0">
      <div className="flex items-center gap-3">
        <div className="flex items-center justify-center w-9 h-9 rounded-lg bg-primary/15">
          <Zap className="w-5 h-5 text-primary" />
        </div>
        <div>
          <h1 className="text-lg font-semibold tracking-tight text-foreground">
            ScriptForge AI
          </h1>
          <p className="text-xs text-foreground/50">
            Transform text into executable scripts
          </p>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 text-xs text-foreground/60">
          <Circle
            className={`w-2.5 h-2.5 fill-current ${
              healthy === null
                ? "text-foreground/30"
                : healthy
                ? "text-accent-green"
                : "text-accent-red"
            }`}
          />
          <span>{healthy === null ? "Checking..." : healthy ? "Online" : "Offline"}</span>
        </div>
        <a
          href="https://github.com"
          target="_blank"
          rel="noopener noreferrer"
          className="text-foreground/40 hover:text-foreground/70 transition-colors"
        >
          <Github className="w-5 h-5" />
        </a>
      </div>
    </header>
  );
}
