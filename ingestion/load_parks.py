"""Loads the 63 official National Parks from the NPS Data API into the `parks` table.

Run separately from the API (see docs/spec.md §4.3) — not part of the live request path.

    uv run python load_parks.py

NOTE: the NPS API's response field names below (parkCode, fullName, designation,
latitude/longitude) are from the documented schema, not independently verified
against a live call (this environment can't reach nps.gov). Sanity-check the
printed park count and a sample record the first time this runs against a real key.
"""

import sys

import httpx
import psycopg

from config import settings

NPS_API_BASE = "https://developer.nps.gov/api/v1/parks"
PAGE_SIZE = 500


def fetch_all_parks() -> list[dict]:
    parks = []
    start = 0
    with httpx.Client(headers={"X-Api-Key": settings.nps_api_key}, timeout=30) as client:
        while True:
            response = client.get(NPS_API_BASE, params={"limit": PAGE_SIZE, "start": start})
            response.raise_for_status()
            payload = response.json()
            batch = payload["data"]
            parks.extend(batch)
            total = int(payload["total"])
            start += len(batch)
            if start >= total or not batch:
                break
    return parks


# Two of the 63 official National Parks don't match on designation/name text:
# - npsa (American Samoa): NPS leaves `designation` blank for this one.
# - redw (Redwood): officially "Redwood National and State Parks" -- the word
#   order means the substring "National Park" never appears in the full name.
MANUAL_INCLUDE_PARK_CODES = {"npsa", "redw"}

# NPS represents Sequoia and Kings Canyon as a single combined API record
# (parkCode "seki", designation "National Parks"), but they're officially
# counted as 2 separate parks in every published "63 National Parks" list,
# including this app's own passport (see docs/phase1-notes.md). Split the one
# API record into two synthetic entries so the passport can reach a true 63/63.
COMBINED_PARK_SPLITS = {
    "seki": [
        {"parkCode": "seki-sequoia", "fullName": "Sequoia National Park"},
        {"parkCode": "seki-kings", "fullName": "Kings Canyon National Park"},
    ]
}


def filter_national_parks(all_parks: list[dict]) -> list[dict]:
    return [
        p
        for p in all_parks
        if "National Park" in p.get("designation", "")
        or p.get("parkCode") in MANUAL_INCLUDE_PARK_CODES
    ]


def expand_combined_parks(national_parks: list[dict]) -> list[dict]:
    expanded = []
    for p in national_parks:
        splits = COMBINED_PARK_SPLITS.get(p.get("parkCode"))
        if splits is None:
            expanded.append(p)
        else:
            expanded.extend({**p, **split} for split in splits)
    return expanded


def upsert_parks(national_parks: list[dict]) -> None:
    with psycopg.connect(settings.database_url) as conn, conn.cursor() as cur:
        for p in national_parks:
            cur.execute(
                """
                INSERT INTO parks (nps_park_code, name, states, description, lat, lng)
                VALUES (%(code)s, %(name)s, %(states)s, %(description)s, %(lat)s, %(lng)s)
                ON CONFLICT (nps_park_code) DO UPDATE SET
                    name = EXCLUDED.name,
                    states = EXCLUDED.states,
                    description = EXCLUDED.description,
                    lat = EXCLUDED.lat,
                    lng = EXCLUDED.lng
                """,
                {
                    "code": p["parkCode"],
                    "name": p["fullName"],
                    "states": p["states"],
                    "description": p["description"],
                    "lat": float(p["latitude"]),
                    "lng": float(p["longitude"]),
                },
            )
        conn.commit()


def main() -> None:
    print("Fetching all NPS park units...")
    all_parks = fetch_all_parks()
    print(f"Fetched {len(all_parks)} total park units.")

    national_parks = expand_combined_parks(filter_national_parks(all_parks))
    print(f"Filtered to {len(national_parks)} National Parks (expected: 63).")
    if len(national_parks) != 63:
        print(
            "WARNING: expected exactly 63 — the designation filter may need adjusting. "
            "Sample designations found:",
            sorted({p.get("designation", "") for p in national_parks}),
            file=sys.stderr,
        )

    upsert_parks(national_parks)
    print("Done.")


if __name__ == "__main__":
    main()
