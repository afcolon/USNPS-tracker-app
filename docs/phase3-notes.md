# Phase 3 — Trip Planner v1 (Greedy) Notes

Spec §7 defines "done" for Phase 3 as: *"Given park + days, returns a reasonable
day-by-day plan, no travel-time optimization yet."* Spec §5 gives the v1 algorithm
shape: filter by difficulty, sort by a quality/duration blend, greedily pack into
days respecting an hours budget, no travel-time optimization (that's v2/Phase 4).

## Decisions made with you (confirmed via prompts)

| Area | Choice | Why |
|---|---|---|
| Trip persistence | Persist to DB (`Trip`/`TripItineraryItem`, spec §6) | Matches the data model sketch; lets a user look back at past plans later. |
| Frontend UI | Build it now, not deferred | Unlike Phase 2's data-only scope, the trip planner *is* the feature's user-facing value. |

**Noted follow-up, explicitly not in Phase 3 scope:** allow a user to delete/clean
up a saved itinerary (`DELETE /trips/{id}`). Flagged by you during scoping; there's
no UI or endpoint for this yet.

## The greedy algorithm, concretely (`backend/app/planner.py`)

The spec describes the v1 approach in prose; here's exactly what that became,
since "sort by some blend of highlight quality and duration" and "respecting a
max-hours-per-day budget" both needed a concrete formula:

- **Quality score:** `avg_rating * log(reviews_count + 1)`. Chosen so a single
  5-star/3-review hike doesn't outrank a 4.8-star/40,000-review one -- directly
  uses the `avg_rating`/`reviews_count` fields added in the Phase 5 scope decision
  (see `docs/phase2-notes.md`), which is exactly what they were added for.
- **Bin-packing:** hikes are considered highest-quality-first; each goes into
  whichever day both has room for it and would have the least leftover budget
  afterward (best-fit decreasing). This packs days tightly rather than spreading
  hikes thin across every day before any one is full. A hike that doesn't fit
  anywhere within budget is dropped from the itinerary -- v1 has no overflow
  handling (e.g. a second shorter trip, or relaxing the budget).
- **Duration fallback:** when a hike has no `estimated_duration_min` (e.g. Angels
  Landing -- AllTrails gave none, see `docs/phase2-notes.md`), falls back to
  `distance_miles * 30 + elevation_gain_ft / 50` -- a rough "30 min/mile pace plus
  a minute per 50 ft of climb" heuristic, not from the spec. Exists only so a
  hike with missing duration data doesn't silently vanish from every itinerary.
- **Difficulty filtering** uses the *effective* difficulty (`difficulty_override`
  when set, else `difficulty`) -- so Angels Landing is correctly excluded by an
  "easy" or "moderate" cap despite its raw computed difficulty being Moderate.

### Geographic ordering is implemented but currently inert

Spec §5 v1 says "just chronological/geographic clustering (e.g. group hikes near
the same trailhead area)" as the alternative to full travel-time optimization
(that's v2/Phase 4). `_order_by_proximity()` does a greedy nearest-neighbor
ordering by trailhead lat/lng within each day -- real code, unit-tested, ready to
use.

But: every hike loaded so far shares its park's centroid as a placeholder
trailhead coordinate (the Phase 2 limitation documented in `docs/phase2-notes.md`
-- AllTrails doesn't expose real trailhead coordinates). So right now this
function runs against identical coordinates for every hike in a park, which is a
no-op (zero distances, order unchanged). It'll start doing real work the moment
real per-trailhead coordinates land (the OSM/NPS-GIS pass planned for Phase 5) --
no code change needed here when that happens.

## Implementation decisions made without asking (documented for easy tweaking)

- **Simplified "thin coverage" warning.** Spec §5 suggests *"limited hike data
  available for this park — showing N of an expected M hikes."* We have no way
  to know "expected M" (that would need knowing the park's true total trail
  count, which nothing in this app tracks). Simplified to: warn whenever
  `len(hikes) < num_days`, naming just the actual count available, e.g. *"Only 5
  hike(s) available for this park -- some days may be light or empty."*
- **`GET /trips/{id}` doesn't recompute or store the warning** -- it's a
  POST-response-only field (`None` on GET). Recomputing it at read-time would
  need "hikes available now" vs. "hikes available at creation," which isn't
  meaningfully different for v1 and adds complexity for no real benefit yet.
- **Every day 1..num_days appears in the response, even empty ones** (e.g. a
  2-day trip with only 1 hike shows Day 1 with the hike and Day 2 explicitly
  empty, not just a 1-item `days` array). Caught while writing the endpoint:
  the first version only emitted days that had an itinerary item, silently
  collapsing empty trailing days -- fixed before any test asserted the wrong
  (more convenient to produce, less useful to show) behavior.
- **Extracted `get_current_user` into `app/deps.py`.** It was duplicated as a
  private helper in `app/api/parks.py`; `app/api/trips.py` needed the same
  thing, so this was the point to deduplicate rather than copy-paste again.
- **Only Zion is meaningfully plannable right now.** Trip planning works for any
  park, but only Zion has hike data loaded (Phase 2's pilot). Planning a trip
  for any other park returns a 201 with all-empty days and the thin-coverage
  warning -- correct behavior, just not a very interesting demo until Phase 5
  expands hike coverage to more parks.
- **No new frontend dependency (no router).** The trip planner is a second
  "view" toggled via local state in `App.tsx` (`planningPark: Park | null`),
  not a route -- consistent with the app having no router at all so far, and
  avoids adding one for what's currently just two views.

## Caught by the pre-merge review (CLAUDE.md convention), before merging

Four real findings from the standing pre-merge review pass, all fixed before
this branch was merged:

- **A genuine showstopper:** `created_at` was inserted as a timezone-aware
  datetime (`datetime.now(datetime.UTC)`) into a column declared timezone-naive
  (`sa.DateTime()`). asyncpg (real Postgres) rejects this outright --
  `POST /trips` would 500 on every call in production. Completely invisible in
  the test suite because SQLite doesn't enforce the distinction -- all 21 tests
  passed while the endpoint was broken for its actual target database. Fixed by
  declaring the column `DateTime(timezone=True)` in both the migration and the
  model (confirmed via `alembic upgrade head --sql`: now emits
  `TIMESTAMP WITH TIME ZONE`).
- **The thin-coverage warning compared the wrong count.** It checked raw
  `len(hikes)` against `num_days`, so a park with plenty of hikes that all get
  filtered out by `max_difficulty` (or don't fit any day's `max_hours_per_day`
  budget) produced a silently empty itinerary with no warning. Fixed to compare
  the actually-*scheduled* hike count instead.
- **Check-then-use race + a redundant query** in `GET /trips/{id}`: it checked
  existence with `db.get()`, then re-queried the same row via `scalar_one()` in
  the shared loader, which would 500 instead of 404 if the row vanished between
  the two calls, and always cost two round trips for one logical read. Merged
  into a single `scalar_one_or_none()` fetch, reused by both POST and GET.
- **`num_days` had no validation** -- `POST /trips` with `num_days=0` (or
  negative) was accepted and silently produced an empty, persisted trip instead
  of a 422. Added `Field(gt=0, le=30)`; `max_hours_per_day` got the same
  treatment (`gt=0`).

## Full-stack verification — needs you

Same Docker constraint as every prior phase: this sandbox can't run Postgres, so
this is verified by unit tests (22 backend tests, all passing) and a clean
frontend build/lint/format only, not a real end-to-end run yet:

- ⬜ `alembic upgrade head` creating the `trips`/`trip_itinerary_items` tables
- ⬜ `POST /trips` for Zion returns a real itinerary with Angels Landing etc.,
  respecting difficulty/hours-per-day filters
- ⬜ `GET /trips/{id}` retrieves a previously created trip
- ⬜ Frontend: click "Plan a trip" on Zion's card, submit the form, see a
  day-by-day itinerary; confirm the "Plan a trip" button doesn't also toggle
  the visited stamp (separate click targets, `stopPropagation` on the inner
  button)

```bash
cd backend && uv run alembic upgrade head && uv run uvicorn app.main:app --reload
# frontend already running via ./scripts/dev.sh, or separately:
cd frontend && npm run dev
```
