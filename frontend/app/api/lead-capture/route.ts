import { NextResponse } from "next/server";

/**
 * POST /api/lead-capture
 *
 * Accepts { email: string } and stores it for later use.
 * Currently logs to console — ready to hook into Resend, Mailchimp, or a DB.
 */
export async function POST(request: Request) {
  try {
    const body = await request.json();
    const email = typeof body?.email === "string" ? body.email.trim() : "";

    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      return NextResponse.json(
        { error: "Please provide a valid email address." },
        { status: 400 },
      );
    }

    // ── Store the lead ────────────────────────────────────────────
    // TODO: Replace with your email provider (Resend, Mailchimp, etc.)
    // Example: await resend.emails.send({ ... });
    // Example: await db.insert(leads).values({ email, createdAt: new Date() });
    console.log(`[Lead Capture] New lead: ${email}`);

    return NextResponse.json({ status: "success" }, { status: 200 });
  } catch {
    return NextResponse.json(
      { error: "Internal server error." },
      { status: 500 },
    );
  }
}
