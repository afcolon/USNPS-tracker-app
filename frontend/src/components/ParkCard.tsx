import type { Park } from '../types';

interface ParkCardProps {
  park: Park;
  onToggleVisited: (park: Park) => void;
  onPlanTrip: (park: Park) => void;
}

export function ParkCard({ park, onToggleVisited, onPlanTrip }: ParkCardProps) {
  return (
    <div className={`park-card${park.visited ? ' park-card--visited' : ''}`}>
      <button type="button" className="park-card__main" onClick={() => onToggleVisited(park)}>
        {park.visited && <span className="park-card__stamp">✓ Visited</span>}
        <h3 className="park-card__name">{park.name}</h3>
        <p className="park-card__states">{park.states}</p>
        {park.visited_date && <p className="park-card__date">{park.visited_date}</p>}
      </button>
      <button
        type="button"
        className="park-card__plan-trip"
        onClick={(e) => {
          e.stopPropagation();
          onPlanTrip(park);
        }}
      >
        Plan a trip →
      </button>
    </div>
  );
}
