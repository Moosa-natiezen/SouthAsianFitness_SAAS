#!/usr/bin/env python3
"""Simulate a Lemon Squeezy subscription_created webhook.

Sends a signed POST to the local FastAPI server and verifies the target
user's subscription_tier is updated to 'pro' in the database.

Usage:
    1. Make sure the FastAPI server is running on localhost:8000
    2. python scripts/test_webhook.py
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import sys
from pathlib import Path

import requests
from sqlalchemy import create_engine, text

# ── Configuration ─────────────────────────────────────────────────────

WEBHOOK_URL = "http://localhost:8000/api/billing/webhook"
WEBHOOK_SECRET = "test_secret_123"
TARGET_USER_ID = "6bb466ee-0687-4e5e-8bda-7f8bf77a82fb"
TARGET_EMAIL = "mmoosaqureshi@gmail.com"

# ── Load DATABASE_URL from root .env ──────────────────────────────────

DATABASE_URL: str | None = None
env_path = Path(__file__).resolve().parent.parent / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        if line.startswith("DATABASE_URL="):
            DATABASE_URL = line.split("=", 1)[1].strip()
            break

if not DATABASE_URL:
    DATABASE_URL = os.environ.get("DATABASE_URL", "")
if not DATABASE_URL:
    print("ERROR: DATABASE_URL not found in .env or environment")
    sys.exit(1)


# ── Step 1: Check current user tier ───────────────────────────────────

def get_user_tier(user_id: str) -> str | None:
    """Query the database for the user's current subscription tier."""
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT subscription_tier FROM users WHERE id = :uid"),
            {"uid": user_id},
        )
        row = result.first()
        return row[0] if row else None


print("=" * 60)
print("LEMON SQUEEZY WEBHOOK SIMULATION TEST")
print("=" * 60)

current_tier = get_user_tier(TARGET_USER_ID)
print(f"\n1. Current tier for {TARGET_EMAIL}: {current_tier}")

if current_tier == "pro":
    print("   ⚠ User is already Pro. Downgrading to 'free' for test...")
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        conn.execute(
            text("UPDATE users SET subscription_tier = 'free' WHERE id = :uid"),
            {"uid": TARGET_USER_ID},
        )
        conn.commit()
    print("   ✓ Downgraded to 'free'")


# ── Step 2: Build the mock webhook payload ─────────────────────────────

payload = {
    "meta": {
        "event_name": "subscription_created",
        "custom_data": {
            "user_id": TARGET_USER_ID,
        },
    },
    "data": {
        "type": "subscriptions",
        "id": "sub_1234567890",
        "attributes": {
            "customer_id": 99999,
            "id": "sub_1234567890",
            "user_email": TARGET_EMAIL,
            "status": "active",
            "renews_at": "2026-12-01T00:00:00Z",
            "urls": {
                "customer_portal": "https://app.lemonsqueezy.com/my subscriptions/portal/123",
            },
            "custom_data": {
                "user_id": TARGET_USER_ID,
            },
        },
    },
}

raw_body = json.dumps(payload).encode("utf-8")

print(f"\n2. Webhook payload built ({len(raw_body)} bytes)")
print(f"   Event: {payload['meta']['event_name']}")
print(f"   User ID: {payload['meta']['custom_data']['user_id']}")


# ── Step 3: Sign the payload ──────────────────────────────────────────

signature = hmac.new(
    WEBHOOK_SECRET.encode("utf-8"),
    raw_body,
    hashlib.sha256,
).hexdigest()

print(f"\n3. HMAC-SHA256 signature computed: {signature[:32]}...")


# ── Step 4: Send the webhook ──────────────────────────────────────────

print(f"\n4. Sending POST to {WEBHOOK_URL}")

try:
    response = requests.post(
        WEBHOOK_URL,
        data=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Signature": signature,
        },
        timeout=10,
    )
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text[:200]}")
except requests.ConnectionError:
    print("   ✗ CONNECTION REFUSED — Is the FastAPI server running?")
    print("     Start it with: cd backend && uv run uvicorn app.main:app --reload")
    sys.exit(1)


# ── Step 5: Verify the database was updated ───────────────────────────

if response.status_code == 200:
    new_tier = get_user_tier(TARGET_USER_ID)
    print(f"\n5. Database check after webhook:")
    print(f"   User: {TARGET_EMAIL}")
    print(f"   Tier before: {current_tier}")
    print(f"   Tier after:  {new_tier}")

    if new_tier == "pro":
        print("\n   SUCCESS — User upgraded to Pro!")
    else:
        print(f"\n   FAILURE — Expected 'pro', got '{new_tier}'")
        sys.exit(1)
else:
    print(f"\n   Webhook failed with status {response.status_code}")
    sys.exit(1)

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
