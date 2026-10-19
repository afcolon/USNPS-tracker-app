import type { Park, Trip, TripRequest } from './types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

export async function fetchParks(): Promise<Park[]> {
  const res = await fetch(`${API_BASE_URL}/parks`);
  if (!res.ok) throw new Error('Failed to fetch parks');
  return res.json();
}

export async function markVisited(parkId: number, visitedDate: string): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/parks/${parkId}/visit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ visited_date: visitedDate }),
  });
  if (!res.ok) throw new Error('Failed to mark park visited');
}

export async function unmarkVisited(parkId: number): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/parks/${parkId}/visit`, { method: 'DELETE' });
  if (!res.ok) throw new Error('Failed to unmark park visited');
}

export async function createTrip(request: TripRequest): Promise<Trip> {
  const res = await fetch(`${API_BASE_URL}/trips`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  if (!res.ok) throw new Error('Failed to create trip');
  return res.json();
}

export async function getTrip(tripId: number): Promise<Trip> {
  const res = await fetch(`${API_BASE_URL}/trips/${tripId}`);
  if (!res.ok) throw new Error('Failed to fetch trip');
  return res.json();
}
