"use client";

import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { fetchHealth, type HealthResponse } from "@/lib/api";

type LoadState =
  | { status: "loading" }
  | { status: "ready"; data: HealthResponse }
  | { status: "error"; message: string };

export function BackendStatus() {
  const [state, setState] = useState<LoadState>({ status: "loading" });

  useEffect(() => {
    let cancelled = false;

    fetchHealth()
      .then((data) => {
        if (!cancelled) {
          setState({ status: "ready", data });
        }
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          const message =
            error instanceof Error ? error.message : "Unable to reach the backend";
          setState({ status: "error", message });
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const connected =
    state.status === "ready" &&
    state.data.api === "ok" &&
    state.data.database === "connected";

  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle>Backend connection</CardTitle>
        <CardDescription>
          Live status from <code className="text-xs">GET /api/health</code>
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {state.status === "loading" && (
          <p className="text-sm text-muted-foreground">Checking backend…</p>
        )}

        {state.status === "error" && (
          <div className="space-y-2">
            <Badge variant="destructive">Disconnected</Badge>
            <p className="text-sm text-muted-foreground">{state.message}</p>
          </div>
        )}

        {state.status === "ready" && (
          <div className="space-y-3">
            <Badge variant={connected ? "default" : "secondary"}>
              {connected ? "Connected" : "Degraded"}
            </Badge>
            <ul className="space-y-1 text-sm">
              <li>API: {state.data.api}</li>
              <li>Database: {state.data.database}</li>
              <li>Overall: {state.data.status}</li>
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
