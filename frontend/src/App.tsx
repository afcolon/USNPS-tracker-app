import { useEffect, useState } from 'react';
import { fetchParks, getTrip, markVisited, unmarkVisited } from './api';
import { ParkCard } from './components/ParkCard';
import { TripPlanner } from './components/TripPlanner';
import type { Park, Trip } from './types';

const TOTAL_NATIONAL_PARKS = 63;

function parseTripIdFromUrl(): number | null {
  const raw = new URLSearchParams(window.location.search).get('trip');
  if (!raw) return null;
  const id = Number(raw);
  return Number.isFinite(id) ? id : null;
}

function App() {
  const [parks, setParks] = useState<Park[]>([]);
  const [parksLoaded, setParksLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [planningPark, setPlanningPark] = useState<Park | null>(null);
  const [linkedTrip, setLinkedTrip] = useState<Trip | null>(null);
  const [linkedTripId, setLinkedTripId] = useState<number | null>(() => parseTripIdFromUrl());

  useEffect(() => {
    fetchParks()
      .then((fetched) => {
        setParks(fetched);
        setParksLoaded(true);
      })
      .catch(() => setError('Could not load parks. Is the backend running?'));
  }, []);

  useEffect(() => {
    if (linkedTripId == null) return;
    getTrip(linkedTripId)
      .then(setLinkedTrip)
      .catch(() => setError('Could not load the linked trip. It may no longer exist.'));
  }, [linkedTripId]);

  const linkedPark = linkedTrip ? (parks.find((p) => p.id === linkedTrip.park_id) ?? null) : null;
  const activePark = planningPark ?? linkedPark;
  const linkedTripUnresolved = linkedTrip != null && parksLoaded && linkedPark == null;

  async function handleToggleVisited(park: Park) {
    try {
      if (park.visited) {
        await unmarkVisited(park.id);
      } else {
        await markVisited(park.id, new Date().toISOString().slice(0, 10));
      }
      setParks(await fetchParks());
    } catch {
      setError('Could not update that park. Try again.');
    }
  }

  if (activePark) {
    return (
      <TripPlanner
        park={activePark}
        onBack={() => {
          setPlanningPark(null);
          setLinkedTrip(null);
          setLinkedTripId(null);
        }}
        initialTrip={linkedTrip ?? undefined}
      />
    );
  }

  if (linkedTripUnresolved) {
    return (
      <main className="passport">
        <p className="passport__error">Could not find the park for this trip.</p>
        <button
          type="button"
          onClick={() => {
            setLinkedTrip(null);
            setLinkedTripId(null);
          }}
        >
          Back to passport
        </button>
      </main>
    );
  }

  if (linkedTripId != null && !error) {
    return (
      <main className="passport">
        <p>Loading your trip…</p>
      </main>
    );
  }

  const visitedCount = parks.filter((p) => p.visited).length;

  return (
    <main className="passport">
      <header className="passport__header">
        <h1>National Parks Passport</h1>
        <p className="passport__progress">
          {visitedCount} of {TOTAL_NATIONAL_PARKS} visited
        </p>
      </header>

      {error && <p className="passport__error">{error}</p>}

      {parks.length === 0 && !error && <p>Loading parks…</p>}

      <div className="passport__grid">
        {parks.map((park) => (
          <ParkCard
            key={park.id}
            park={park}
            onToggleVisited={handleToggleVisited}
            onPlanTrip={setPlanningPark}
          />
        ))}
      </div>
    </main>
  );
}

export default App;
