# National Parks Passport & Trip Planner — Spec Document

**Working title:** *Trailhead Passport* (placeholder — rename freely)
**Status:** Draft v1
**Author:** Alex

---

## 1. Vision

A personal app that combines two things:

1. **A passport / tracker** — mark U.S. National Parks as visited, unlock an icon/stamp for each one, and see visual progress toward "visiting them all."
2. **A trip planner** — given a park and a number of days, recommend a set of hikes to build an itinerary from, using official NPS data for hike stats and aggregated review/blog data for qualitative info (highlights, vibe), with travel time between trailheads factored into the plan.

This is a solo/portfolio project, so the spec below is written to be buildable incrementally, with each phase shippable and testable on its own — not one big bang.

---

## 2. Core Features

### 2.1 Park Passport
- Scope: the 63 official "National Park" designated sites only — no monuments, historic sites, seashores, etc. **(decided)**
- User can mark a park as **visited** (with optional visit date, notes, photos later)
- Visited parks display a unique icon/stamp on a passport-style grid or map view
- Progress view: X of 63 visited, map heat/fill view, maybe a % complete badge

### 2.2 Trip Planner
- User selects a park + trip length in days
- App recommends a set of hikes for that trip, factoring in:
  - Hike stats (distance, incline, difficulty, type)
  - Estimated time per hike (derived from distance/incline, or scraped where available)
  - **Travel time between trailheads**, so the itinerary doesn't zigzag across the park
  - Some notion of "don't overload one day" (e.g. total mileage/elevation budget per day)
- Output: a day-by-day itinerary (Day 1: Hike A + Hike B, Day 2: Hike C, ...)

### 2.3 Hike Data
Each hike record includes:
| Field | Source | Notes |
|---|---|---|
| Distance (miles) | Computed from OpenStreetMap trail geometry (primary), NPS GIS data (cross-check) | See §3.2 — computed rather than trusted from any single third party |
| Elevation gain (ft) | Computed from OSM path + USGS elevation data | Same rationale — computed, not scraped |
| Difficulty rating | Computed score, mapped to **NPS's Easy/Moderate/Strenuous scale** | Strictly NPS's 3-tier scale — see §3.2.1 for the mapping approach |
| Type | Inferred from OSM path topology | Loop vs. out-and-back vs. point-to-point |
| Highlights | Aggregated from openly-licensed text sources (Wikipedia/Wikivoyage, OSM points of interest, permissively-licensed sites) | Short bullet summary — "waterfall at mile 2", "best sunset spot", etc. Manual entry only where no usable source exists |
| Trailhead location | OSM / NPS GIS data | Needed for travel-time calculations |

### 2.4 Out of scope for v1 (explicitly deferred)
- Social features (sharing passports, following friends)
- Offline/mobile app (start web-only, responsive)
- Real-time trail conditions / closures (NPS Alerts API could be a v2 addition)
- Booking integration (camping, permits)

---

## 3. Data Sources

### 3.1 National Park Service (NPS) API + GIS data
- Free, official, requires an API key: https://www.nps.gov/subjects/developer/api-documentation.htm
- Provides park metadata, some "things to do" and "places" (including trail-adjacent points of interest)
- NPS also publishes GIS/geospatial data (trail centerlines, boundaries) through its data portal (irma.nps.gov / data.nps.gov / NPS ArcGIS hub) for many parks — worth pulling directly where available, since it's the most authoritative trailhead/trail-geometry source when it exists.
- **Caveat:** coverage is inconsistent across parks — some have rich data, others have almost none. This is exactly why §3.2 below is the primary path rather than a fallback.

### 3.2 Aggregated data (primary approach — decided)

**Decision:** aggregated sources are the primary path for hike data, with manual entry used only where no usable aggregated source exists for a given park. This also solves a second problem you flagged: inconsistent stats *between* sources. Rather than trusting whichever third party reports a number, the plan **computes** distance, elevation gain, and difficulty directly from geodata, so every hike is measured the same way regardless of park:

1. **OpenStreetMap (via the Overpass API)** — the trail geometry backbone. This is free, has no restrictive ToS beyond attribution (ODbL license), covers essentially every U.S. national park, and is notably the same base layer AllTrails itself builds on. From a trail's path geometry you can compute exact distance and infer type (loop vs. out-and-back vs. point-to-point) directly, instead of trusting an inconsistent reported number.
2. **USGS elevation data (SRTM/3DEP digital elevation models)** — free and public domain. Sampling elevation along the OSM path gives you a computed elevation gain, again consistent across every hike rather than however each blog rounded it.
3. **NPS GIS data** (§3.1) — used to cross-check/prioritize official trail geometry where NPS has published it, before falling back to general OSM coverage.
4. **Highlights text** — sourced from openly-licensed content: Wikipedia and Wikivoyage entries (CC BY-SA, attribution required), OSM point-of-interest tags along a route (viewpoints, waterfalls, summits — tagged as `natural=*`, `tourism=viewpoint`, etc.), and any specific sources you individually confirm are permissively licensed or public domain (e.g. NPS's own trail descriptions). This deliberately avoids AllTrails/Reddit/most blogs, which either restrict API access or have ToS that block automated collection.
5. **Manual entry — last resort only:** for the (likely small) set of park trails where OSM coverage is sparse and no licensed highlight text exists, enter data by hand. Track a `source` field per hike record (`osm_computed`, `nps_gis`, `manual`) so the app — and you — always know how reliable a given entry is, and so the recommendation engine (§5) can down-weight or flag manually-entered gaps rather than silently treating all hikes as equally well-measured.

### 3.2.1 Difficulty rating — mapping to NPS's scale (decided)

NPS uses a 3-tier scale: **Easy / Moderate / Strenuous**. Since stats are computed (not scraped per-source), difficulty should be computed too, then bucketed into these 3 tiers — rather than trying to reconcile every third party's own difficulty label after the fact.

A simple, well-established approach: a **hiking difficulty formula** that combines distance and elevation gain into one score, e.g. the Shenandoah-style formula:

```
difficulty_score = sqrt(elevation_gain_ft × 2 × distance_miles)
```

Bucket the resulting score into NPS's 3 tiers (exact thresholds to tune against a handful of real NPS-rated hikes as validation — e.g. pick a few hikes NPS has explicitly labeled "Strenuous" and confirm the formula agrees):

| Score range (example starting point) | NPS tier |
|---|---|
| < 50 | Easy |
| 50 – 150 | Moderate |
| > 150 | Strenuous |

**Common mismatches to expect when other sources disagree**, and how to resolve them:
| Other source's label | Likely cause of mismatch | Resolution |
|---|---|---|
| AllTrails "Hard" | AllTrails uses a 3-tier scale (Easy/Moderate/Hard) but weights differently and factors in trail surface/exposure, not just distance/gain | Trust the computed score over the imported label; treat the source label as a secondary signal only |
| Blogs using 4–5 tier scales (e.g. "Difficult", "Very Difficult", "Extreme") | Finer-grained scales don't map 1:1 to NPS's 3 tiers | Collapse to nearest NPS tier using the computed score, not the source's word choice |
| Sources rating by *time* or *exposure/exposure risk* rather than distance/elevation | Some trails are short but strenuous due to scrambling, altitude, or heat exposure, which a distance/gain formula won't capture | Flag these as a manual-override case rather than trusting the formula blindly — worth a `difficulty_override` field for known exceptions |

Where NPS has *already* published an official difficulty label for a hike, that always wins — the computed/mapped score is only used to fill gaps where NPS hasn't rated a trail.

### 3.3 Travel time between trailheads
- Google Maps Distance Matrix API (paid past free tier, very accurate) or OSRM (open-source, self-hostable, free) for driving time between trailhead coordinates.
- For a portfolio project, OSRM is worth considering since it avoids API costs and keys, though Google's data is more reliable for real-world routing (closures, actual road network).

---

## 4. Architecture & Stack Recommendation

### 4.1 Should it be Python?

Short answer: **yes, for the parts that matter most here** — but you don't have to build the whole thing in Python.

The two hardest problems in this app are (1) reconciling messy hike data from multiple sources and (2) building a trip-recommendation engine that reasons about distance/time/difficulty tradeoffs. Both are squarely in Python's strengths — data wrangling (pandas), text summarization/NLP if you go the review-aggregation route, and optimization/scheduling logic (there are mature libraries like `ortools` for exactly the "pack N hikes into D days factoring travel time" problem).

You've also already built a Spring Boot + React project ([[portfolio-microservice-project]]), so you have real Java/React experience. Worth naming the actual tradeoff:

| | Python (FastAPI) end-to-end | Java (Spring Boot) + Python data service |
|---|---|---|
| Learning value | New language for backend work — broadens your portfolio | Reuses what you just built; less new surface area |
| Data/recommendation logic | Native — pandas, ortools, easy scripting | Requires a second service or calling out to Python anyway |
| Complexity for a solo dev | Lower — one language, one deploy | Higher — two services, two deploy pipelines, a boundary to design |
| Portfolio story | "Built a full-stack Python app with a real recommendation engine" | "Built a polyglot system" — impressive, but more moving parts to maintain solo |

**Recommendation:** build it end-to-end in Python with **FastAPI** for the backend. It keeps one language across the whole app (simpler for a solo dev to maintain and easier for you to reason about while learning), and it puts the recommendation engine — the most interesting part of this project — in the language best suited for it. Keep React for the frontend since you already know it.

If down the road you specifically want to practice polyglot/microservice architecture again, splitting the recommendation engine into its own Python service behind your Spring Boot app is a reasonable v2 move — but it's added complexity you don't need to take on for v1.

### 4.2 Suggested stack

| Layer | Recommendation | Why |
|---|---|---|
| Backend API | Python + FastAPI | Async support, automatic OpenAPI docs, lightweight compared to Django for an API-first app |
| Database | PostgreSQL | Relational fits this data well (parks, hikes, users, visits, trips); PostGIS extension is useful later for geo-queries |
| ORM | SQLAlchemy (+ Alembic for migrations) | Standard pairing with FastAPI |
| Frontend | React (Vite) | You already have this experience |
| Data ingestion | Python scripts / a small `ingestion/` package, run on a schedule or manually | Keep separate from the API app — different concern, different cadence |
| Travel time | OSRM (self-hosted via Docker) or Google Distance Matrix | Start with OSRM to avoid API costs while prototyping |
| Recommendation engine | Python, starting with a simple greedy/heuristic algorithm, `ortools` if you outgrow it | See §5 |
| Hosting (later) | Containerized (Docker), deployable to Render/Fly.io/a VPS | You already containerize with Docker/Nginx in your other project — same pattern applies |

### 4.3 High-level architecture

```
┌─────────────┐      ┌──────────────────┐      ┌──────────────┐
│   React     │◄────►│   FastAPI app     │◄────►│  PostgreSQL  │
│  frontend   │      │  (API + rec       │      │              │
└─────────────┘      │   engine)         │      └──────────────┘
                      └────────┬──────────┘
                               │
                      ┌────────▼──────────┐
                      │  Ingestion scripts │  (run separately,
                      │  NPS API, curated  │   not part of the
                      │  hike data, OSRM   │   live request path)
                      └────────────────────┘
```

Keep ingestion out of the live request path — it should populate your database on its own schedule, so a user checking off a park never waits on a scrape/API call to a third party.

---

## 5. Trip Recommendation Engine — Approach

This is the feature most worth being deliberate about, since it's the differentiator.

**Inputs:** park, number of days, (optionally) user preferences like difficulty tolerance or max daily mileage.

**Data needed per hike:** distance, incline, difficulty, estimated duration, trailhead coordinates.

**Accounting for data gaps and confidence:** since coverage will vary by park (§3.2), the engine shouldn't treat every hike record as equally trustworthy. Two lightweight mechanisms to build in from the start rather than bolt on later:
- Carry the `source` field (`osm_computed`, `nps_gis`, `manual`) through to the recommendation layer, and prefer higher-confidence hikes when scores are close.
- For parks with thin coverage, surface that to the user explicitly in the trip output (e.g. "limited hike data available for this park — showing N of an expected M hikes") rather than silently returning a sparse or skewed itinerary.

**Suggested build order (don't start with optimization):**

1. **v1 — Greedy/manual rules:** For the chosen park, filter hikes by difficulty preference, sort by some blend of "highlight quality" and duration, and manually group into days respecting a max-hours-per-day budget. No travel-time optimization yet — just chronological/geographic clustering (e.g. group hikes near the same trailhead area).
2. **v2 — Add travel time:** Build a distance/time matrix between trailheads (via OSRM), and use it to avoid itineraries that zigzag. A reasonable non-fancy approach: cluster trailheads geographically first (e.g. k-means on coordinates), then assign clusters to days.
3. **v3 — Real optimization (optional/stretch):** Frame it as a variant of a vehicle routing / knapsack problem — maximize "value" (highlight quality, variety) within daily time and mileage budgets, minimizing travel time between selected hikes. `ortools` (Google's constraint solver) is the natural tool if you get here.

Starting simple and testable at each stage fits your general approach of building incrementally and testing between steps — the greedy version is a real, demoable feature on its own, and you can decide later whether the optimization step is worth the added complexity.

---

## 6. Data Model (initial sketch)

```
Park
  id, name, nps_park_code, state(s), description, lat, lng

Hike
  id, park_id (FK), name, distance_miles, elevation_gain_ft,
  difficulty (NPS scale: easy/moderate/strenuous), difficulty_score,
  difficulty_override (nullable), hike_type (loop/out_and_back/point_to_point),
  trailhead_lat, trailhead_lng, estimated_duration_min,
  source (osm_computed/nps_gis/manual)

HikeHighlight
  id, hike_id (FK), text, source_url

User
  id, name, email, ...

VisitedPark  (the "passport" entries)
  id, user_id (FK), park_id (FK), visited_date, notes

Trip
  id, user_id (FK), park_id (FK), num_days, created_at

TripItineraryItem
  id, trip_id (FK), hike_id (FK), day_number, order_in_day
```

---

## 7. Suggested Build Phases

| Phase | Goal | Done when... |
|---|---|---|
| 0 | Project scaffolding | FastAPI app + React app talk to each other; Postgres running in Docker |
| 1 | Park data + passport | All NPS parks loaded from the NPS API; user can mark visited, sees stamps |
| 2 | Hike data (curated, 1 pilot park) | Hikes for one park manually entered with full stats + highlights |
| 3 | Trip planner v1 (greedy) | Given park + days, returns a reasonable day-by-day plan, no travel-time logic yet |
| 4 | Travel time integration | Itinerary respects trailhead proximity (OSRM matrix) |
| 5 | Expand hike data coverage | More parks, decide on curation vs. aggregation approach from §3.2 |
| 6 (stretch) | Optimization engine | Replace greedy logic with `ortools`-based solver |

---

## 8. Decisions Log

| # | Question | Decision |
|---|---|---|
| 1 | Hike data coverage gap | Aggregated sources (OSM + USGS + NPS GIS) are primary; manual entry only where no usable source exists. Stats are computed, not scraped, to also fix cross-source inconsistency — see §3.2 |
| 2 | Restricted sources (AllTrails, etc.) | Avoided. Using OpenStreetMap, USGS elevation data, NPS GIS data, and openly-licensed text (Wikipedia/Wikivoyage) instead — see §3.2 |
| 3 | Which parks count for the passport | The 63 official National Parks only — no monuments/historic sites — see §2.1 |
| 4 | Difficulty scale mismatches | Strictly NPS's Easy/Moderate/Strenuous scale; other sources' ratings are mapped in via a computed distance+elevation formula, with NPS's own rating always taking precedence when it exists — see §3.2.1 |

## 9. Open Questions / Risks still to resolve

- **Difficulty formula thresholds:** the score-to-tier cutoffs in §3.2.1 are a starting point — need validation against real NPS-rated hikes before trusting them broadly.
- **OSM coverage variance:** even though OSM covers most trails, coverage quality (completeness, tagging detail) will still vary by park — worth spot-checking a few less-visited parks (not just the popular ones) before assuming §3.2's approach scales cleanly to all 63.
- **Wikipedia/Wikivoyage highlight coverage:** likely strong for iconic parks (Yellowstone, Yosemite) and thin for less-visited ones (e.g. Isle Royale, Gates of the Arctic) — the manual-entry fallback in §3.2 will probably concentrate in these parks; worth sizing that effort once you see real coverage numbers.
- **Difficulty override cases:** trails where distance/elevation formulas mislead (scrambling, altitude, heat exposure) need identifying park-by-park — likely an ongoing curation task rather than a one-time setup step.

---

## 10. Next Steps

1. Get an NPS API key and prototype pulling data for one park, including a check of what NPS GIS trail data actually exists for it.
2. Prototype the OSM + USGS computed-stats pipeline for a single well-mapped trail, and sanity-check the numbers against NPS's own published stats for that trail (where NPS has them).
3. Scaffold the FastAPI + React + Postgres project (Phase 0).
4. Build the passport feature first — it's the simplest end-to-end slice and gets the full stack wired up before tackling the harder recommendation logic.
