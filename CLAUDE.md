# Project conventions

National Parks Passport & Trip Planner. Full spec: `docs/spec.md`. Build phases and
their decisions/verification status are tracked in `docs/phaseN-notes.md`.

## Branching and merging

- Each phase (or significant feature) gets its own branch (`phase-N-description`),
  pushed to `origin` as work progresses.
- **No pull requests.** The user reviews branches manually and merges locally — do
  not open a PR unless explicitly asked to.
- Merge into `main` with a fast-forward merge (`git merge --ff-only`) once the user
  has reviewed and approved the branch, not by rebasing/squashing or force-pushing.

## Pre-merge code review (standing convention)

**Before merging any branch into `main`, run an independent review pass** — invoke
the `/code-review` skill (or spawn a review subagent) against the diff vs `main` —
and surface the findings to the user before merging, even if you (Claude) wrote the
code yourself in the same conversation. The point is a second, less-attached pass
that can catch what the implementing context missed.

- Report findings; don't silently auto-fix. The user decides what to act on vs.
  accept as a known tradeoff (consistent with how every other judgment call in this
  project gets made — see the `docs/phaseN-notes.md` decision logs).
- This replaces, not supplements, your own judgment — if the review pass finds
  nothing, say so plainly rather than padding the report.
- This is a manual step performed as part of the merge workflow, not automated CI —
  there's no GitHub Actions workflow doing this independently. If that ever changes,
  update this section.

## Local dev

- `./scripts/dev.sh` — starts Postgres + backend + frontend together, Ctrl-C stops
  all three. Assumes one-time setup is already done (see root `README.md`).
- `./scripts/load-data.sh` — one-off: loads all 63 National Parks + Zion's pilot
  hike data. Needs Postgres up and migrated, and `ingestion/.env` with a real
  `NPS_API_KEY`.

## Commit messages

End every commit with:
```
Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_011KZFzMtFp8oqyNwvXtNhKK
```
(Check the current session's actual attribution lines if this ever runs under a
different session — don't assume this exact URL is still correct.)
