# Phase 3 — Trip Planner v1 (Greedy) Notes

Spec §7 defines "done" for Phase 3 as: *"Given park + days, returns a reasonable
day-by-day plan, no travel-time optimization yet."* Spec §5 gives the v1 algorithm
shape: filter by difficulty, sort by a quality/duration blend, greedily pack into
days respecting an hours budget, no travel-time optimization (that's v3/Phase 5).

## Decisions made with you (confirmed via prompts)

| Area | Choice | Why |
|---|---|---|
| Trip persistence | Persist to DB (`Trip`/`TripItineraryItem`, spec §6) | Matches the data model sketch; lets a user look back at past plans later. |
| Frontend UI | Build it now, not deferred | Unlike Phase 2's data-only scope, the trip planner *is* the feature's user-facing value. |
| Revisiting a saved trip | `?trip=<id>` query param via `history.pushState`, no router library | Caught during manual verification: trips were persisted but nothing in the UI ever surfaced the id, so a "saved" trip was unreachable once you navigated away -- defeating the point of persisting it. Query param keeps the "no router yet" decision (see below) while making a trip bookmarkable/shareable: `App.tsx` reads `?trip=` on load, fetches it, and resolves the owning park from the already-loaded parks list; `TripPlanner` pushes `?trip=<id>` onto the URL right after a successful `POST /trips`. |

**Noted follow-up, explicitly not in Phase 3 scope:** allow a user to delete/clean
up a saved itinerary (`DELETE /trips/{id}`). Flagged by you during scoping; there's
no UI or endpoint for this yet.

## The greedy algorithm, concretely (`backend/app/planner.py`)

The spec describes the v1 approach in prose; here's exactly what that became,
since "sort by some blend of highlight quality and duration" and "respecting a
max-hours-per-day budget" both needed a concrete formula:

- **Quality score:** `avg_rating * log(reviews_count + 1)`. Chosen so a single
  5-star/3-review hike doesn't outrank a 4.8-star/40,000-review one -- directly
  uses the `avg_rating`/`reviews_count` fields added in the Phase 6 scope decision
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
(that's v3/Phase 5). `_order_by_proximity()` does a greedy nearest-neighbor
ordering by trailhead lat/lng within each day -- real code, unit-tested, ready to
use.

But: every hike loaded so far shares its park's centroid as a placeholder
trailhead coordinate (the Phase 2 limitation documented in `docs/phase2-notes.md`
-- AllTrails doesn't expose real trailhead coordinates). So right now this
function runs against identical coordinates for every hike in a park, which is a
no-op (zero distances, order unchanged). It'll start doing real work the moment
real per-trailhead coordinates land (the OSM/NPS-GIS pass planned for Phase 6) --
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
  warning -- correct behavior, just not a very interesting demo until Phase 6
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
  budget) produced a silently empty itinerary with no warning. First fix pass
  corrected the *trigger* condition but left the message text reporting the
  same stale raw count while claiming it "match[ed] your preferences" -- caught
  on the very next review pass. Now both the trigger and the message use the
  actually-*scheduled* count.
- **A bare `assert` guarding a "this should never happen" case** (the just-
  committed trip failing to reload) would silently no-op under `-O`/
  `PYTHONOPTIMIZE`, turning a would-be clear error into an obscure
  `AttributeError` deeper in `_trip_to_out`. Replaced with an explicit
  `HTTPException(500, ...)` that survives optimization flags.
- **Check-then-use race + a redundant query** in `GET /trips/{id}`: it checked
  existence with `db.get()`, then re-queried the same row via `scalar_one()` in
  the shared loader, which would 500 instead of 404 if the row vanished between
  the two calls, and always cost two round trips for one logical read. Merged
  into a single `scalar_one_or_none()` fetch, reused by both POST and GET.
- **`num_days` had no validation** -- `POST /trips` with `num_days=0` (or
  negative) was accepted and silently produced an empty, persisted trip instead
  of a 422. Added `Field(gt=0, le=30)`; `max_hours_per_day` got the same
  treatment (`gt=0`).

## Second pre-merge review pass (after full-stack verification)

Run after real-hardware verification surfaced the `?trip=<id>` gap (see
decisions table above) and the `scripts/dev.sh` fix, to cover that new diff
too. Four more findings; outcomes below.

- **Fixed: stuck "Loading your trip…" state.** Reproduced by you: opening a
  trip via `?trip=<id>` then clicking "Back to passport" left the app stuck
  on the loading screen forever. Root cause -- `onBack` cleared `linkedTrip`
  but `linkedTripId` (parsed once from the URL at mount) had no setter and
  was never reset, so the `linkedTripId != null` loading-guard stayed true
  permanently even with the URL already cleared. Fixed by exposing and
  clearing a `setLinkedTripId` alongside the other reset calls.
- **Fixed: itinerary showed "duration unknown" for hikes the planner had
  actually estimated.** The bin-packer always computes an effective duration
  (`estimate_duration_min` -- real value if present, else the pace/elevation
  fallback) to decide what fits in a day's budget, but that computed value
  never left the backend; the UI only ever saw the possibly-null raw
  `estimated_duration_min` and showed "unknown" regardless of what actually
  drove the packing. Added `TripHikeOut` (extends `HikeOut` with
  `effective_duration_min: int`, always populated) so `TripDayOut.hikes`
  carries what the planner actually used; the UI now shows e.g. "~34m
  (estimated)" instead of "duration unknown" for Canyon-Overlook-style hikes
  with no source duration. Kept as a separate schema rather than changing
  `HikeOut` itself, since `GET /parks/{id}/hikes` has no such reason to claim
  a duration it doesn't have.
- **Noted, not fixed now:** `DIFFICULTY_ORDER.index(...)` in
  `build_itinerary` raises an unhandled `ValueError` (-> 500) if a hike's
  effective difficulty is ever anything other than exactly
  `easy`/`moderate`/`strenuous` -- nothing in the schema enforces that today.
  Latent, not currently reachable with the seeded/loaded data. Flagged to
  revisit once the full hike-ingestion pass (ingesting beyond Zion) is
  underway, since that's the point new difficulty values would actually get
  introduced.
- **Fixed: thin-coverage warning now also catches budget-dropped hikes.**
  Previously it only fired on `scheduled_count < num_days`, missing the case
  where plenty of hikes exist but some don't fit any day's hour budget while
  every day still ends up non-empty. You flagged that a *full* fix (e.g.
  letting a user manually move hikes between days) is out of scope for now --
  that's a future itinerary-editing feature. Scoped the fix to just the
  warning: extracted `filter_by_difficulty()` out of `build_itinerary()` so
  the endpoint can independently compute how many hikes were *eligible*
  (post-difficulty-filter) vs. actually *scheduled*. Now warns with a
  distinct message in each case: too few hikes available for the day count,
  vs. hikes that didn't fit the hours/day budget and were dropped.

## Third pre-merge review pass (after the warning-logic change)

Run again since the warning fix above was itself new code since the last
pass. Three findings.

- **Fixed: a day could end up silently empty even with every eligible hike
  scheduled.** Best-fit-decreasing tends to concentrate hikes into the
  earliest day(s) it can, because each placement picks whichever day leaves
  the *least* leftover budget -- verified against real Zion data (5 hikes,
  3 days: landed as 4/1/0) and reproduced minimally in tests with 3 identical
  2.5h hikes against an 8h/day budget, all landing on day 1. Neither of the
  other two warning triggers catches this (`scheduled_count` can equal both
  `num_days` and `eligible_hikes` while a day is still empty). Added a third
  warning case naming the specific empty day(s).
- **Fixed: the same stuck-"Loading your trip…" bug class, re-exposed via a
  different trigger.** Not "trip loaded, URL state never reset on back" (the
  earlier fix) but "trip loaded fine, but its `park_id` isn't in the loaded
  `parks` list" -- previously fell through to the generic loading branch
  forever, since nothing treated an unresolvable park as an error. Added a
  dedicated `linkedTripUnresolved` branch (derived during render, no
  `setState`-in-effect) with an explicit "Back to passport" action, rather
  than another effect-driven auto-recovery.
- **Fixed: redundant difficulty filtering.** The endpoint computed
  `eligible_hikes` via the newly-extracted `filter_by_difficulty()`, then
  passed the original unfiltered `hikes` into `build_itinerary()`, which
  filters again internally -- same O(n) work done twice per request. Now
  passes `eligible_hikes` straight into `build_itinerary()`; its own internal
  filter call becomes a cheap no-op pass over the already-filtered list
  rather than re-scanning every hike for the park.

## Fourth pre-merge review pass (after the empty-day/stuck-loading fixes)

Four more findings; you chose which to fix now vs. accept as known tradeoffs.

- **Fixed: reopening a saved trip didn't sync the planner form.** The
  itinerary shown via `?trip=<id>` was always correct, but the form fields
  (Days, Max difficulty, Max hours/day) stayed at hardcoded defaults instead
  of the settings the trip was actually created with -- clicking "Plan my
  trip" again would silently replace it using the wrong settings. Root
  cause: `max_difficulty`/`max_hours_per_day` were accepted by `POST /trips`
  but never persisted, so there was nothing to sync from. Added both as
  columns on `Trip` (new migration `8c1f2e9a4b3d`, `max_hours_per_day`
  backfilled to `8.0` for any pre-existing rows), returned them on `TripOut`,
  and initialize `TripPlanner`'s form state from `initialTrip` when present.
- **Fixed: a third trigger for the stuck "Loading your trip…" bug.** If the
  parks table is genuinely empty (e.g. a fresh DB before `load-data.sh`
  runs) while a `?trip=` link is open, `fetchParks()` resolves successfully
  with `[]` -- not an error -- so the old `parks.length > 0` check used to
  detect "parks have loaded" never became true. Added a dedicated
  `parksLoaded` boolean set once the fetch resolves, independent of count.
- **Accepted as a known tradeoff (not fixed):** `createTrip()` failures all
  show the same generic "Is the backend running?" message, including a
  legitimate 422 from the backend's own validation (e.g. clearing the Days
  field to 0). Real but lower priority than the other three; revisit if it
  causes actual confusion in practice.
- **Accepted as a known tradeoff (not fixed):** no DB index on
  `trip_itinerary_items.trip_id`/`hike_id`. Every `GET`/`POST /trips`
  currently joins through these via `selectinload`, which will degrade to a
  sequential scan as the table grows -- not a concern at this app's current
  scale (single user, a handful of trips), revisit if that changes.

## Fifth pre-merge review pass

- **Fixed: `max_hours_per_day` had no upper bound.** It had a floor (`gt=0`)
  but nothing stopping e.g. `99999`, which would silently remove the per-day
  budget as a real constraint and let the bin-packer cram every eligible
  hike into day 1. Added `le=24` (a hard physical ceiling -- the frontend's
  own `<input>` already caps entry at 16, this just backstops the API).
  Same validation-gap class already fixed for `num_days` and this field's
  lower bound.

**Noted as future improvements, not fixed now (your call):**

- The hike query in `create_trip` (`select(Hike).where(Hike.park_id == ...)`)
  has no `ORDER BY`, unlike the sibling `list_hikes` endpoint. Row order is
  unspecified on real Postgres (SQLite, which the tests run against, happens
  to preserve insertion order), so `quality_score` ties in the bin-packer's
  `sorted(..., reverse=True)` break on unpredictable DB-internal order --
  identical `POST /trips` requests could produce different saved itineraries
  across calls. Same "passed on SQLite, bites on real Postgres" class as the
  earlier timezone bug. Fix would be adding an explicit `.order_by(Hike.id)`
  (or similar) to that query.
- `create_trip` does a full extra DB round-trip (`_fetch_trip`) after commit
  to rebuild the response, instead of eager-loading `Hike.highlights` up
  front and building the response from data already in memory. Real
  inefficiency, not a correctness bug, and not urgent at the app's current
  single-user scale -- same tradeoff class as the missing `trip_itinerary_items`
  index noted above.

## Feedback from real-hardware testing (before the fifth review pass's fix landed)

Two issues you hit directly while testing, both fixed:

- **The generic error message was masking the `max_hours_per_day` validation
  error you just hit.** `createTrip()` threw the same `Error` for every
  failure, so the new `le=24` validation (added this pass) surfaced as "Is
  the backend running?" instead of saying what was actually wrong -- this
  was the exact "accepted tradeoff" from the fourth review pass, now worth
  fixing since it directly confused real testing. Added a distinct
  `TripValidationError` thrown specifically on a 422 response, and
  `TripPlanner` now shows "One of your trip settings is invalid -- check the
  days and hours/day values" for that case instead of the generic message.
- **Text was hard to read against a near-black background.** `:root` had
  `color-scheme: light dark`, which lets the browser swap to a dark default
  page background on a dark-mode OS/browser, while every color in
  `index.css` (e.g. the gray `.trip-planner__link` text) was chosen assuming
  a light background -- low contrast, not full invisibility, hence easy to
  miss in review. Short-term fix per your steer (stay consistent, design
  dark mode properly later): pinned `color-scheme: light` and gave `body` an
  explicit white background/dark text color, so the app renders the same
  light theme regardless of OS/browser preference until real dark-mode
  support is designed.

## Full-stack verification — needs you

Same Docker constraint as every prior phase: this sandbox can't run Postgres, so
this is verified by unit tests (22 backend tests, all passing) and a clean
frontend build/lint/format only, not a real end-to-end run yet:

- ✅ `alembic upgrade head` creating the `trips`/`trip_itinerary_items` tables
- ✅ `POST /trips` for Zion returns a real itinerary with Angels Landing etc.,
  respecting difficulty/hours-per-day filters -- verified with `max_difficulty`
  set to Zion's full range, including the "strenuous" cap that includes
  Angels Landing and the newer Observation Point hike
- ✅ `GET /trips/{id}` retrieves a previously created trip -- loading
  `?trip=8` fresh reopened the same Day 1/Day 2 itinerary
- ✅ Frontend: "Plan a trip" on Zion's card, submit the form, day-by-day
  itinerary renders correctly
- ✅ After creating a trip, the URL updates to `?trip=<id>` (confirmed
  `?trip=8` after a hard refresh); reloading that URL reopens the same
  itinerary instead of the parks grid
- ✅ Repeat-use/timezone-fix check: multiple trips created successfully in a
  row against real Postgres (trip ids climbed past 8 across the session) --
  the `DateTime(timezone=True)` fix holds under the real asyncpg driver,
  not just SQLite tests

Also fixed during this verification pass (see decisions table above and
commit history): `./scripts/dev.sh` was silently aborting before printing
anything, due to `set -euo pipefail` being incompatible with sourcing
`nvm.sh`; and saved trips had no way to be revisited from the UI, fixed via
the `?trip=<id>` URL mechanism.

### Still needs you: re-verify after the fourth review pass

The checks above were run before the fourth review pass added a new
migration and the form-sync behavior. Needs one more pass on real hardware
before merging:

- ⬜ `cd backend && uv run alembic upgrade head` picks up the new
  `8c1f2e9a4b3d` migration (`max_difficulty`/`max_hours_per_day` columns on
  `trips`) cleanly on top of the already-applied `34bacf04e5fc`
- ⬜ Create a trip with a difficulty cap and a non-default hours/day, open it
  via its `?trip=<id>` link (or a fresh reload), and confirm the form fields
  now show those actual settings instead of the hardcoded defaults
- ⬜ Confirm the itinerary still shows "~Nm (estimated)" for hikes with no
  real duration data, and a plain duration otherwise
- ⬜ Entering an hours/day value over 24 now shows "One of your trip settings
  is invalid -- check the days and hours/day values" instead of "Is the
  backend running?"
- ⬜ The app renders with a consistent light background/text regardless of
  your OS/browser dark-mode setting (the trip-saved note and other text
  should be clearly readable)

```bash
cd backend && uv run alembic upgrade head && uv run uvicorn app.main:app --reload
# frontend already running via ./scripts/dev.sh, or separately:
cd frontend && npm run dev
```
