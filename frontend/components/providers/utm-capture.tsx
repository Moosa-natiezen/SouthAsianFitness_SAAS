"use client";

import { useEffect } from "react";

import { captureUtms } from "@/lib/utm";

/**
 * Captures UTM parameters from the URL query string on first paint and
 * persists them (sessionStorage + localStorage) so the signup form can
 * pass attribution to the backend. Renders nothing.
 */
export function UtmCapture() {
  useEffect(() => {
    captureUtms();
  }, []);

  return null;
}
