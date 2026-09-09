import { useEffect, useState } from 'react';
import { fetchParks, markVisited, unmarkVisited } from './api';
import { ParkCard } from './components/ParkCard';
import type { Park } from './types';

const TOTAL_NATIONAL_PARKS = 63;

function App() {
  const [parks, setParks] = useState<Park[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchParks()
      .then(setParks)
      .catch(() => setError('Could not load parks. Is the backend running?'));
  }, []);

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
          <ParkCard key={park.id} park={park} onToggleVisited={handleToggleVisited} />
        ))}
      </div>
    </main>
  );
}

export default App;
