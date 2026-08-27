"""Idempotent seed script for reference data required by the onboarding system.

Creates currencies, countries, and regions from ISO 3166 / ISO 4217 data.
Safe to run multiple times — detects existing records and skips duplicates.

Data sources:
  - pycountry: ISO 3166-1 (countries), ISO 3166-2 (subdivisions), ISO 4217 (currencies)
  - Hardcoded country→currency mapping (ISO 4217)

Usage:
    uv run python -m app.scripts.seed_reference_data
    uv run python app/scripts/seed_reference_data.py --dry-run
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass

import pycountry
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.currency import Currency
from app.models.enums import UnitSystem
from app.models.geography import Country, Region

# ── Country → Currency mapping (ISO 3166-1 alpha-2 → ISO 4217) ────────────
# Comprehensive mapping of countries to their primary currency.
# Source: ISO 4217 maintenance agency, CIA World Factbook.

COUNTRY_CURRENCY_MAP: dict[str, str] = {
    # A
    "AF": "AFN", "AL": "ALL", "DZ": "DZD", "AS": "USD", "AD": "EUR",
    "AO": "AOA", "AI": "USD", "AG": "XCD", "AR": "ARS", "AM": "AMD",
    "AW": "AWG", "AU": "AUD", "AT": "EUR", "AZ": "AZN", "BS": "BSD",
    "BH": "BHD", "BD": "BDT", "BB": "BBD", "BY": "BYN", "BE": "EUR",
    "BZ": "BZD", "BJ": "XOF", "BM": "USD", "BT": "BTN", "BO": "BOB",
    "BQ": "USD", "BA": "BAM", "BW": "BWP", "BR": "BRL", "IO": "USD",
    "BN": "BND", "BG": "BGN", "BF": "XOF", "BI": "BIF", "CV": "CVE",
    "KH": "KHR", "CM": "XAF", "CA": "CAD", "KY": "USD", "CF": "XAF",
    "TD": "XAF", "CL": "CLP", "CN": "CNY", "CO": "COP", "KM": "KMF",
    "CG": "XAF", "CD": "CDF", "CK": "NZD", "CR": "CRC", "CI": "XOF",
    "HR": "EUR", "CU": "CUP", "CW": "ANG", "CY": "EUR", "CZ": "CZK",
    "DK": "DKK", "DJ": "DJF", "DM": "XCD", "DO": "DOP", "EC": "USD",
    "EG": "EGP", "SV": "USD", "GQ": "XAF", "ER": "ERN", "EE": "EUR",
    "SZ": "SZL", "ET": "ETB", "FK": "FKP", "FO": "DKK", "FJ": "FJD",
    "FI": "EUR", "FR": "EUR", "GF": "EUR", "PF": "XPF", "GA": "XAF", "GM": "GMD",
    "GE": "GEL", "DE": "EUR", "GH": "GHS", "GI": "GIP", "GR": "EUR",
    "GL": "DKK", "GD": "XCD", "GP": "EUR", "GU": "USD", "GT": "GTQ",
    "GG": "GBP", "GN": "GNF", "GW": "XOF", "GY": "GYD", "HT": "HTG",
    "HN": "HNL", "HK": "HKD", "HU": "HUF", "IS": "ISK", "IN": "INR",
    "ID": "IDR", "IR": "IRR", "IQ": "IQD", "IE": "EUR", "IM": "GBP",
    "IL": "ILS", "IT": "EUR", "JM": "JMD", "JP": "JPY", "JE": "GBP",
    "JO": "JOD", "KZ": "KZT", "KE": "KES", "KI": "AUD", "KP": "KPW",
    "KR": "KRW", "KW": "KWD", "KG": "KGS", "LA": "LAK", "LV": "EUR",
    "LB": "LBP", "LS": "LSL", "LR": "LRD", "LY": "LYD", "LI": "CHF",
    "LT": "EUR", "LU": "EUR", "MO": "MOP",    "MG": "MGA", "MW": "MWK",
    "MY": "MYR", "MV": "MVR", "ML": "XOF", "MT": "EUR", "MH": "USD",
    "MR": "MRU", "MU": "MUR", "MX": "MXN", "FM": "USD", "MD": "MDL",
    "MC": "EUR", "MN": "MNT", "ME": "EUR", "MS": "XCD", "MA": "MAD",
    "MZ": "MZN", "MM": "MMK", "NA": "NAD", "NR": "AUD", "NP": "NPR",
    "NL": "EUR", "NC": "XPF", "NZ": "NZD", "NI": "NIC", "NE": "XOF",
    "NG": "NGN", "NU": "NZD", "NF": "AUD", "MK": "MKD", "MP": "USD",
    "NO": "NOK", "OM": "OMR", "PK": "PKR", "PW": "USD", "PS": "ILS",
    "PA": "PAB", "PG": "PGK", "PY": "PYG", "PE": "PEN", "PH": "PHP",
    "PN": "NZD", "PL": "PLN", "PT": "EUR", "PR": "USD", "QA": "QAR",
    "RE": "EUR", "RO": "RON", "RU": "RUB", "RW": "RWF", "BL": "EUR",
    "SH": "SHP", "KN": "XCD", "LC": "XCD", "MF": "EUR", "PM": "EUR",
    "VC": "XCD", "WS": "WST", "SM": "EUR", "ST": "STN", "SA": "SAR",
    "SN": "XOF", "RS": "RSD", "SC": "SCR", "SL": "SLL", "SG": "SGD",
    "SX": "ANG", "SK": "EUR", "SI": "EUR", "SB": "SBD", "SO": "SOS",
    "ZA": "ZAR", "SS": "SSP", "ES": "EUR", "LK": "LKR", "SD": "SDG",
    "SR": "SRD", "SJ": "NOK", "SE": "SEK", "CH": "CHF", "SY": "SYP",
    "TW": "TWD", "TJ": "TJS", "TZ": "TZS", "TH": "THB", "TL": "USD",
    "TG": "XOF", "TK": "NZD", "TO": "TOP", "TT": "TTD", "TN": "TND",
    "TR": "TRY", "TM": "TMT", "TC": "USD", "TV": "AUD", "UG": "UGX",
    "UA": "UAH", "AE": "AED", "GB": "GBP", "US": "USD", "UY": "UYU",
    "UZ": "UZS", "VU": "VUV", "VE": "VES", "VN": "VND", "VG": "USD",
    "VI": "USD", "WF": "XPF", "EH": "MAD", "YE": "YER", "ZM": "ZMW",
    "ZW": "ZWL",
}

# Minor units for each currency (defaults to 2)
CURRENCY_MINOR_UNITS: dict[str, int] = {
    "BIF": 0, "CLP": 0, "DJF": 0, "GNF": 0, "ISK": 0, "JPY": 0,
    "KMF": 0, "KRW": 0, "KWD": 3, "OMR": 3, "TND": 3, "VND": 0,
    "XOF": 0, "XAF": 0, "XPF": 0, "XCD": 0, "BHD": 3, "IQD": 3,
    "JOD": 3, "LYD": 3,
    "PEN": 0, "PGK": 2, "PHP": 2, "PLN": 2, "PYG": 0, "RWF": 0,
    "SGD": 2, "THB": 2, "ZAR": 2, "MUR": 2, "NPR": 2, "BTN": 2,
    "ETB": 2, "IRR": 0, "KPW": 0, "MMK": 0, "SYP": 0, "VES": 2,
    "UZS": 0, "BYN": 2, "MDL": 2,
}

# Currency name overrides for currencies that pycountry doesn't name well
CURRENCY_NAME_OVERRIDES: dict[str, str] = {
    "XOF": "CFA Franc BCEAO",
    "XAF": "CFA Franc BEAC",
    "XPF": "CFP Franc",
    "XCD": "East Caribbean Dollar",
    "ANG": "Netherlands Antillean Guilder",
    "SZL": "Eswatini Lilangeni",
    "LSL": "Lesotho Loti",
    "GMD": "Gambian Dalasi",
    "MOP": "Macanese Pataca",
    "MRU": "Mauritanian Ouguiya",
    "STN": "São Tomé and Príncipe Dobra",
    "SSP": "South Sudanese Pound",
}

# Symbol overrides for currencies where pycountry doesn't provide good symbols
CURRENCY_SYMBOL_OVERRIDES: dict[str, str] = {
    "PKR": "Rs", "INR": "₹", "BDT": "৳", "NPR": "₨", "LKR": "Rs",
    "AED": "د.إ", "SAR": "﷼", "QAR": "﷼", "OMR": "﷼",
    "BHD": "BD", "KWD": "د.ك", "IRR": "﷼", "JOD": "JD",
    "EGP": "E£", "NGN": "₦", "GHS": "GH₵", "ZAR": "R",
    "XOF": "CFA", "XAF": "CFA", "XPF": "₣", "XCD": "$",
    "ANG": "ƒ", "BTN": "Nu.", "ETB": "Br", "MUR": "₨",
    "LAK": "₭", "KHR": "៛", "MNT": "₮", "KZT": "₸",
    "UZS": "сўм", "AZN": "₼", "GEL": "₾", "AMD": "֏",
    "THB": "฿", "IDR": "Rp", "MYR": "RM", "PHP": "₱",
    "VND": "₫", "KRW": "₩", "KPW": "₩", "JPY": "¥",
    "CNY": "¥", "BRL": "R$", "RUB": "₽", "TRY": "₺",
    "ISK": "kr", "SEK": "kr", "NOK": "kr", "DKK": "kr",
    "CZK": "Kč", "PLN": "zł", "HUF": "Ft", "RON": "lei",
    "BGN": "лв", "RSD": "дин", "MKD": "ден", "UAH": "₴",
    "KGS": "сом", "TJS": "ЅМ", "TMT": "T",
    "IQD": "ع.د", "SYP": "£", "LBP": "L£",
    "DZD": "د.ج", "MAD": "MAD", "TND": "د.ت",
    "RWF": "FRw", "TZS": "TSh", "UGX": "USh", "KES": "KSh",
    "SDG": "SDG", "SSP": "SSP",
    "DJF": "Fdj", "KMF": "CF", "SZL": "E", "LSL": "L",
    "MZN": "MT", "AOA": "Kz", "ZMW": "ZK",
    "ZWL": "$", "BWP": "P", "NAD": "N$",
    "CDF": "FC",
    "CAD": "C$", "AUD": "A$", "NZD": "NZ$", "SGD": "S$",
    "HKD": "HK$", "TWD": "NT$", "MOP": "MOP$",
    "GTQ": "Q", "HNL": "L", "NIO": "C$", "CRC": "₡",
    "PEN": "S/", "BOB": "Bs", "VES": "Bs", "PYG": "₲",
    "COP": "$", "CLP": "$", "UYU": "$U", "ARS": "$",
    "DOP": "RD$", "CUP": "₱", "HTG": "G", "JMD": "J$",
    "TTD": "TT$", "BBD": "Bds$", "GYD": "G$", "SRD": "S$",
    "FJD": "FJ$", "PGK": "K", "WST": "T", "TOP": "T$",
    "VUV": "VT", "SBD": "SB$", "BND": "B$",
}

# ── Region type display name mapping (for logging) ──────────────────────────

REGION_TYPE_NAMES: dict[str, str] = {
    "State": "state", "Province": "province", "Region": "region",
    "Division": "division", "Governorate": "governorate",
    "Emirate": "emirate", "Department": "department",
    "County": "county", "Prefecture": "prefecture",
    "Autonomous community": "autonomous community",
    "Canton": "canton", "Land": "state", "Commune": "commune",
    "Federal district": "federal district",
    "Metropolitan city": "metropolitan city",
    "Oblast": "oblast", "Republic": "republic",
    "City": "city", "District": "district", "Territory": "territory",
}


# ── Seed functions ─────────────────────────────────────────────────────────


@dataclass
class SeedResult:
    currencies_created: int = 0
    countries_created: int = 0
    regions_created: int = 0
    currencies_skipped: int = 0
    countries_skipped: int = 0
    regions_skipped: int = 0


def _resolve_currency_data(code: str) -> tuple[str, str, int]:
    """Return (name, symbol, minor_units) for a currency code."""
    # Name
    name = CURRENCY_NAME_OVERRIDES.get(code)
    if not name:
        try:
            cur = pycountry.currencies.get(alpha_3=code)
            name = cur.name if cur else code
        except (AttributeError, LookupError):
            name = code

    # Symbol
    symbol = CURRENCY_SYMBOL_OVERRIDES.get(code, code)

    # Minor units
    minor = CURRENCY_MINOR_UNITS.get(code, 2)

    return name, symbol, minor


def seed_currencies(db: Session) -> SeedResult:
    """Create missing currencies from ISO 4217 data. Idempotent."""
    result = SeedResult()

    # Collect all unique currency codes used by our countries
    used_codes = sorted(set(COUNTRY_CURRENCY_MAP.values()))

    for code in used_codes:
        existing = db.execute(
            select(Currency).where(Currency.code == code)
        ).scalars().first()
        if existing is not None:
            result.currencies_skipped += 1
            continue

        name, symbol, minor_units = _resolve_currency_data(code)
        currency = Currency(
            code=code,
            name=name,
            symbol=symbol,
            minor_units=minor_units,
        )
        db.add(currency)
        result.currencies_created += 1

    db.flush()
    return result


def seed_countries(db: Session) -> SeedResult:
    """Create missing countries from ISO 3166-1. Idempotent."""
    result = SeedResult()

    for alpha2, currency_code in COUNTRY_CURRENCY_MAP.items():
        existing = db.execute(
            select(Country).where(Country.iso_code == alpha2)
        ).scalars().first()
        if existing is not None:
            result.countries_skipped += 1
            continue

        try:
            iso_country = pycountry.countries.get(alpha_2=alpha2)
            name = iso_country.name if iso_country else alpha2
        except (AttributeError, LookupError):
            name = alpha2

        country = Country(
            name=name,
            iso_code=alpha2,
            currency_code=currency_code,
            default_unit_system=UnitSystem.METRIC,
        )
        db.add(country)
        result.countries_created += 1

    db.flush()
    return result


def _deduplicate_subdivisions(subs: list) -> list:
    """Deduplicate subdivisions by name within a country.

    Some ISO 3166-2 entries have duplicate names (e.g., BD has both numeric
    and alpha codes for the same region). Keep only the first occurrence.
    """
    seen_names: set[str] = set()
    unique: list = []
    for sub in subs:
        if sub.name not in seen_names:
            seen_names.add(sub.name)
            unique.append(sub)
    return unique


def seed_regions(db: Session) -> SeedResult:
    """Create missing regions from ISO 3166-2. Idempotent."""
    result = SeedResult()

    # Build a lookup of iso_code → Country.id
    country_rows = db.execute(select(Country)).scalars().all()
    country_id_map: dict[str, object] = {c.iso_code: c.id for c in country_rows}

    # Group subdivisions by country, deduplicate by name
    for alpha2 in sorted(country_id_map.keys()):
        country_id = country_id_map[alpha2]
        subs = _deduplicate_subdivisions(
            [s for s in pycountry.subdivisions if s.country_code == alpha2]
        )

        for sub in subs:
            # Use the ISO 3166-2 code (e.g., US-CA, IN-MH)
            code = sub.code
            name = sub.name

            existing = db.execute(
                select(Region).where(
                    Region.country_id == country_id,
                    Region.code == code,
                )
            ).scalars().first()
            if existing is not None:
                result.regions_skipped += 1
                continue

            region = Region(
                name=name,
                code=code,
                country_id=country_id,
            )
            db.add(region)
            result.regions_created += 1

    db.flush()
    return result


def seed_all(db: Session, *, commit: bool = True) -> SeedResult:
    """Run all seed operations in order: currencies → countries → regions."""
    total = SeedResult()

    # Fast path: if data already seeded, skip expensive per-record queries.
    # This avoids ~5000 individual SELECTs on every container startup.
    expected_currencies = len(set(COUNTRY_CURRENCY_MAP.values()))
    expected_countries = len(COUNTRY_CURRENCY_MAP)
    existing_currencies = db.execute(select(func.count(Currency.code))).scalar() or 0
    existing_countries = db.execute(select(func.count(Country.id))).scalar() or 0
    if existing_currencies >= expected_currencies and existing_countries >= expected_countries:
        total.currencies_skipped = existing_currencies
        total.countries_skipped = existing_countries
        total.regions_skipped = db.execute(select(func.count(Region.id))).scalar() or 0
        return total

    c = seed_currencies(db)
    total.currencies_created += c.currencies_created
    total.currencies_skipped += c.currencies_skipped

    c = seed_countries(db)
    total.countries_created += c.countries_created
    total.countries_skipped += c.countries_skipped

    c = seed_regions(db)
    total.regions_created += c.regions_created
    total.regions_skipped += c.regions_skipped

    if commit:
        db.commit()
    return total


# ── CLI entrypoint ─────────────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Seed reference data (currencies, countries, regions) for onboarding."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be created without committing changes",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    db = SessionLocal()
    try:
        if args.dry_run:
            result = seed_all(db, commit=False)
            mode = "dry-run"
        else:
            result = seed_all(db, commit=True)
            mode = "seed"

        print(f"Mode: {mode}")
        print(f"Currencies: {result.currencies_created} created, {result.currencies_skipped} skipped")
        print(f"Countries:  {result.countries_created} created, {result.countries_skipped} skipped")
        print(f"Regions:    {result.regions_created} created, {result.regions_skipped} skipped")
    except (ValueError, OSError) as exc:
        db.rollback()
        print(f"Seed failed: {exc}", file=sys.stderr)
        return 1
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
