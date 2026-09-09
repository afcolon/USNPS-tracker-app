import type { Park } from '../types';

interface ParkCardProps {
  park: Park;
  onToggleVisited: (park: Park) => void;
}

export function ParkCard({ park, onToggleVisited }: ParkCardProps) {
  return (
    <button
      type="button"
      className={`park-card${park.visited ? ' park-card--visited' : ''}`}
      onClick={() => onToggleVisited(park)}
    >
      {park.visited && <span className="park-card__stamp">✓ Visited</span>}
      <h3 className="park-card__name">{park.name}</h3>
      <p className="park-card__states">{park.states}</p>
      {park.visited_date && <p className="park-card__date">{park.visited_date}</p>}
    </button>
  );
}
