export interface Park {
  id: number;
  nps_park_code: string;
  name: string;
  states: string;
  description: string;
  lat: number;
  lng: number;
  visited: boolean;
  visited_date: string | null;
}

export interface HikeHighlight {
  text: string;
  source_url: string | null;
}

export interface Hike {
  id: number;
  name: string;
  distance_miles: number;
  elevation_gain_ft: number;
  difficulty: string;
  difficulty_score: number;
  difficulty_override: string | null;
  difficulty_override_reason: string | null;
  hike_type: string;
  trailhead_lat: number;
  trailhead_lng: number;
  estimated_duration_min: number | null;
  source: string;
  source_url: string | null;
  avg_rating: number | null;
  reviews_count: number | null;
  highlights: HikeHighlight[];
}

export interface TripHike extends Hike {
  effective_duration_min: number;
}

export interface TripDay {
  day_number: number;
  hikes: TripHike[];
}

export interface Trip {
  id: number;
  park_id: number;
  num_days: number;
  max_difficulty: 'easy' | 'moderate' | 'strenuous' | null;
  max_hours_per_day: number;
  created_at: string;
  warning: string | null;
  days: TripDay[];
}

export interface TripRequest {
  park_id: number;
  num_days: number;
  max_difficulty?: 'easy' | 'moderate' | 'strenuous';
  max_hours_per_day?: number;
}
