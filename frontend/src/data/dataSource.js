// dataSource.js — Single data-source abstraction for location data
// Current mode: "mock" (backend not ready)
// Switch to "api" when backend is ready

export const DATA_SOURCE_MODE = 'mock'; // 'mock' | 'api'

// Base URL for future API integration (not used today)
export const API_BASE_URL = 'http://localhost:8000/v1';

// Mock data source — single source of truth for location data
import mockLocations from './mockLocations';

export async function fetchLocations() {
  if (DATA_SOURCE_MODE === 'api') {
    // TODO: Replace with real API call when backend is ready
    // const response = await fetch(`${API_BASE_URL}/locations`);
    // const data = await response.json();
    // return mapApiResponseToLocations(data);
    throw new Error('API mode not implemented yet');
  }
  // Return mock data (simulate async for consistent interface)
  return mockLocations;
}

export async function fetchLocationById(id) {
  if (DATA_SOURCE_MODE === 'api') {
    // TODO: Replace with real API call when backend is ready
    // const response = await fetch(`${API_BASE_URL}/locations/${id}`);
    // const data = await response.json();
    // return mapApiLocationToFrontend(data);
    throw new Error('API mode not implemented yet');
  }
  // Return mock data
  const location = mockLocations.find(loc => loc.id === id);
  if (!location) throw new Error(`Location not found: ${id}`);
  return location;
}

// Placeholder for future API response mapping
// DO NOT implement until backend provides final JSON schema
export function mapApiResponseToLocations(apiResponse) {
  // TODO: Map actual backend response to frontend location shape
  // This is a placeholder - do not implement until backend schema is finalized
  throw new Error('API response mapping not implemented - waiting for backend schema');
}

export function mapApiLocationToFrontend(apiLocation) {
  // TODO: Map single location from backend to frontend shape
  // This is a placeholder - do not implement until backend schema is finalized
  throw new Error('API location mapping not implemented - waiting for backend schema');
}

// Data source status for UI indicator
export function getDataSourceStatus() {
  return {
    mode: DATA_SOURCE_MODE,
    status: DATA_SOURCE_MODE === 'api' ? 'live' : 'cached',
    label: DATA_SOURCE_MODE === 'api' ? 'LIVE' : 'CACHED',
  };
}