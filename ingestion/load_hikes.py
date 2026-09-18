"""Loads curated hike data for a pilot park into the `hikes`/`hike_highlights` tables.

Run separately from the API (see docs/spec.md §4.3) -- not part of the live request path.

    uv run python load_hikes.py data/zion_hikes.json

Unlike load_parks.py, this doesn't call a live API itself -- the source data was
curated interactively via the AllTrails MCP connector (see docs/phase2-notes.md
for why AllTrails, and its limits) and saved as a JSON file. This script just
loads that file into the database, computing each hike's NPS-scale difficulty
per docs/spec.md §3.2.1 along the way.
"""

import json
import math
import sys

import psycopg

from config import settings


def compute_difficulty(distance_miles: float, elevation_gain_ft: float) -> tuple[float, str]:
    """Shenandoah-style difficulty formula from docs/spec.md §3.2.1, bucketed
    into NPS's Easy/Moderate/Strenuous scale."""
    score = math.sqrt(elevation_gain_ft * 2 * distance_miles)
    if score < 50:
        tier = "easy"
    elif score <= 150:
        tier = "moderate"
    else:
        tier = "strenuous"
    return score, tier


def load_hikes(data_path: str) -> None:
    with open(data_path) as f:
        data = json.load(f)

    park_code = data["park_code"]
    default_source = data["source"]

    with psycopg.connect(settings.database_url) as conn, conn.cursor() as cur:
        cur.execute("SELECT id, lat, lng FROM parks WHERE nps_park_code = %s", (park_code,))
        row = cur.fetchone()
        if row is None:
            raise SystemExit(f"No park with code '{park_code}' found -- run load_parks.py first.")
        park_id, trailhead_lat, trailhead_lng = row

        for h in data["hikes"]:
            score, computed_tier = compute_difficulty(h["distance_miles"], h["elevation_gain_ft"])
            difficulty = h.get("difficulty_override") or computed_tier

            cur.execute(
                """
                INSERT INTO hikes (
                    park_id, name, distance_miles, elevation_gain_ft, difficulty,
                    difficulty_score, difficulty_override, difficulty_override_reason,
                    hike_type, trailhead_lat, trailhead_lng, estimated_duration_min,
                    source, source_id, source_url
                )
                VALUES (
                    %(park_id)s, %(name)s, %(distance_miles)s, %(elevation_gain_ft)s,
                    %(difficulty)s, %(difficulty_score)s, %(difficulty_override)s,
                    %(difficulty_override_reason)s, %(hike_type)s, %(trailhead_lat)s,
                    %(trailhead_lng)s, %(estimated_duration_min)s, %(source)s,
                    %(source_id)s, %(source_url)s
                )
                ON CONFLICT (source, source_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    distance_miles = EXCLUDED.distance_miles,
                    elevation_gain_ft = EXCLUDED.elevation_gain_ft,
                    difficulty = EXCLUDED.difficulty,
                    difficulty_score = EXCLUDED.difficulty_score,
                    difficulty_override = EXCLUDED.difficulty_override,
                    difficulty_override_reason = EXCLUDED.difficulty_override_reason,
                    hike_type = EXCLUDED.hike_type,
                    trailhead_lat = EXCLUDED.trailhead_lat,
                    trailhead_lng = EXCLUDED.trailhead_lng,
                    estimated_duration_min = EXCLUDED.estimated_duration_min,
                    source_url = EXCLUDED.source_url
                RETURNING id
                """,
                {
                    "park_id": park_id,
                    "name": h["name"],
                    "distance_miles": h["distance_miles"],
                    "elevation_gain_ft": h["elevation_gain_ft"],
                    "difficulty": difficulty,
                    "difficulty_score": score,
                    "difficulty_override": h.get("difficulty_override"),
                    "difficulty_override_reason": h.get("difficulty_override_reason"),
                    "hike_type": h["hike_type"],
                    "trailhead_lat": trailhead_lat,
                    "trailhead_lng": trailhead_lng,
                    "estimated_duration_min": h.get("estimated_duration_min"),
                    "source": default_source,
                    "source_id": h["source_id"],
                    "source_url": h.get("source_url"),
                },
            )
            hike_id = cur.fetchone()[0]

            # No stable ID per highlight -- replace the set on each load.
            cur.execute("DELETE FROM hike_highlights WHERE hike_id = %s", (hike_id,))
            for text in h.get("highlights", []):
                cur.execute(
                    "INSERT INTO hike_highlights (hike_id, text, source_url) VALUES (%s, %s, %s)",
                    (hike_id, text, h.get("source_url")),
                )

            print(f"{h['name']}: {difficulty} (score {score:.1f})")

        conn.commit()

    print(f"Loaded {len(data['hikes'])} hikes for {park_code}.")


if __name__ == "__main__":
    load_hikes(sys.argv[1] if len(sys.argv) > 1 else "data/zion_hikes.json")
