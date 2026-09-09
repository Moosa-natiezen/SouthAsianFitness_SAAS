import { ImageResponse } from "next/og";

export const alt = "South Asian Fitness — AI Meal Plans & Macro Tracking";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function OpengraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          background: "#FCFBF7",
          position: "relative",
        }}
      >
        {/* Soft emerald corner glows */}
        <div
          style={{
            position: "absolute",
            top: -120,
            left: -120,
            width: 420,
            height: 420,
            borderRadius: 9999,
            background: "rgba(5,150,105,0.10)",
          }}
        />
        <div
          style={{
            position: "absolute",
            bottom: -120,
            right: -120,
            width: 420,
            height: 420,
            borderRadius: 9999,
            background: "rgba(5,150,105,0.10)",
          }}
        />

        {/* Logo mark */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            width: 96,
            height: 96,
            borderRadius: 24,
            background: "#059669",
            color: "#ffffff",
            fontSize: 36,
            fontWeight: 700,
            boxShadow: "0 12px 32px rgba(5,150,105,0.25)",
          }}
        >
          SA
        </div>

        {/* Headline */}
        <div
          style={{
            marginTop: 40,
            fontSize: 68,
            fontWeight: 700,
            color: "#1C1917",
            letterSpacing: -1,
          }}
        >
          South Asian Fitness
        </div>

        {/* Sub-headline */}
        <div
          style={{
            marginTop: 16,
            fontSize: 30,
            color: "#78716C",
            display: "flex",
          }}
        >
          AI meal plans for the food you actually eat.
        </div>

        {/* Emerald accent rule */}
        <div
          style={{
            marginTop: 36,
            width: 120,
            height: 6,
            borderRadius: 9999,
            background: "#059669",
          }}
        />
      </div>
    ),
    { ...size },
  );
}
