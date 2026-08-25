"""Public endpoint to serve available countries and regions with real database UUIDs."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.geography import Country, Region

router = APIRouter(prefix="/locations", tags=["locations"])


class RegionOut(BaseModel):
    id: str
    name: str
    code: str | None


class CountryOut(BaseModel):
    id: str
    name: str
    iso_code: str
    currency_code: str
    regions: list[RegionOut]


@router.get("/", response_model=list[CountryOut])
def list_countries(db: Session = Depends(get_db)) -> list[CountryOut]:
    """Return all countries with their regions.

    This is a public endpoint — no authentication required.
    The frontend uses these real UUIDs to submit onboarding data.
    """
    countries = db.query(Country).order_by(Country.name).all()
    result: list[CountryOut] = []
    for c in countries:
        regions = (
            db.query(Region)
            .filter(Region.country_id == c.id)
            .order_by(Region.name)
            .all()
        )
        result.append(
            CountryOut(
                id=str(c.id),
                name=c.name,
                iso_code=c.iso_code,
                currency_code=c.currency_code,
                regions=[
                    RegionOut(id=str(r.id), name=r.name, code=r.code)
                    for r in regions
                ],
            )
        )
    return result
