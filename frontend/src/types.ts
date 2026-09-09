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
