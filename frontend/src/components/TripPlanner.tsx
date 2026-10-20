import { useState } from 'react';
import { createTrip } from '../api';
import type { Hike, Park, Trip, TripRequest } from '../types';

interface TripPlannerProps {
  park: Park;
  onBack: () => void;
  initialTrip?: Trip;
}

const DIFFICULTIES: NonNullable<TripRequest['max_difficulty']>[] = [
  'easy',
  'moderate',
  'strenuous',
];

function effectiveDifficulty(hike: Hike): string {
  return hike.difficulty_override ?? hike.difficulty;
}

function formatDuration(hike: Hike): string {
  if (hike.estimated_duration_min == null) return 'duration unknown';
  const hours = Math.floor(hike.estimated_duration_min / 60);
  const minutes = hike.estimated_duration_min % 60;
  return hours > 0 ? `${hours}h ${minutes}m` : `${minutes}m`;
}

export function TripPlanner({ park, onBack, initialTrip }: TripPlannerProps) {
  const [numDays, setNumDays] = useState(2);
  const [maxDifficulty, setMaxDifficulty] = useState<string>('');
  const [maxHoursPerDay, setMaxHoursPerDay] = useState(8);
  const [trip, setTrip] = useState<Trip | null>(initialTrip ?? null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  function handleBack() {
    const url = new URL(window.location.href);
    url.searchParams.delete('trip');
    window.history.pushState({}, '', url);
    onBack();
  }

  async function handlePlan() {
    setLoading(true);
    setError(null);
    try {
      const result = await createTrip({
        park_id: park.id,
        num_days: numDays,
        max_difficulty: maxDifficulty
          ? (maxDifficulty as NonNullable<TripRequest['max_difficulty']>)
          : undefined,
        max_hours_per_day: maxHoursPerDay,
      });
      setTrip(result);
      const url = new URL(window.location.href);
      url.searchParams.set('trip', String(result.id));
      window.history.pushState({}, '', url);
    } catch {
      setError('Could not plan a trip. Is the backend running?');
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="trip-planner">
      <button type="button" className="trip-planner__back" onClick={handleBack}>
        ← Back to passport
      </button>
      <h1>Plan a trip: {park.name}</h1>

      <div className="trip-planner__form">
        <label>
          Days
          <input
            type="number"
            min={1}
            max={14}
            value={numDays}
            onChange={(e) => setNumDays(Number(e.target.value))}
          />
        </label>
        <label>
          Max difficulty
          <select value={maxDifficulty} onChange={(e) => setMaxDifficulty(e.target.value)}>
            <option value="">Any</option>
            {DIFFICULTIES.map((d) => (
              <option key={d} value={d}>
                {d}
              </option>
            ))}
          </select>
        </label>
        <label>
          Max hours/day
          <input
            type="number"
            min={1}
            max={16}
            value={maxHoursPerDay}
            onChange={(e) => setMaxHoursPerDay(Number(e.target.value))}
          />
        </label>
        <button type="button" onClick={handlePlan} disabled={loading}>
          {loading ? 'Planning…' : 'Plan my trip'}
        </button>
      </div>

      {error && <p className="trip-planner__error">{error}</p>}

      {trip && (
        <div className="trip-planner__itinerary">
          <p className="trip-planner__link">
            Saved as trip #{trip.id} — this page's URL now links back to it.
          </p>
          {trip.warning && <p className="trip-planner__warning">{trip.warning}</p>}
          {trip.days.map((day) => (
            <div key={day.day_number} className="trip-day">
              <h2>Day {day.day_number}</h2>
              {day.hikes.length === 0 && <p className="trip-day__empty">No hikes scheduled.</p>}
              <ul>
                {day.hikes.map((hike) => (
                  <li key={hike.id} className="trip-day__hike">
                    <strong>{hike.name}</strong> — {hike.distance_miles} mi,{' '}
                    {hike.elevation_gain_ft} ft gain, {effectiveDifficulty(hike)},{' '}
                    {formatDuration(hike)}
                    {hike.avg_rating != null && <> · {hike.avg_rating}★</>}
                    {hike.highlights.length > 0 && (
                      <ul className="trip-day__highlights">
                        {hike.highlights.map((h, i) => (
                          <li key={i}>{h.text}</li>
                        ))}
                      </ul>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}
    </main>
  );
}
