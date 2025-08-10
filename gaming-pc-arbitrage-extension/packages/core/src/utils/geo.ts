/**
 * Geographic Utilities
 * Distance calculations and location helpers
 */

export interface Coordinates {
  lat: number;
  lng: number;
}

/**
 * Calculate distance between two coordinates using Haversine formula
 * @returns Distance in miles
 */
export function calculateDistance(from: Coordinates, to: Coordinates): number {
  const R = 3959; // Earth's radius in miles
  const dLat = toRadians(to.lat - from.lat);
  const dLng = toRadians(to.lng - from.lng);
  
  const a = 
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(toRadians(from.lat)) * Math.cos(toRadians(to.lat)) *
    Math.sin(dLng / 2) * Math.sin(dLng / 2);
  
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

/**
 * Check if a location is within radius of center
 */
export function isWithinRadius(
  center: Coordinates,
  location: Coordinates,
  radiusMiles: number
): boolean {
  const distance = calculateDistance(center, location);
  return distance <= radiusMiles;
}

/**
 * Convert degrees to radians
 */
function toRadians(degrees: number): number {
  return degrees * (Math.PI / 180);
}

/**
 * Generate Google Maps URL for directions
 */
export function getDirectionsUrl(from: Coordinates, to: Coordinates): string {
  return `https://www.google.com/maps/dir/?api=1&origin=${from.lat},${from.lng}&destination=${to.lat},${to.lng}`;
}

/**
 * Generate Google Maps URL for a location
 */
export function getLocationUrl(location: Coordinates): string {
  return `https://www.google.com/maps/search/?api=1&query=${location.lat},${location.lng}`;
}

/**
 * Parse location string to extract city and state
 */
export function parseLocation(locationString: string): { city: string; state: string } {
  const parts = locationString.split(',').map(s => s.trim());
  return {
    city: parts[0] || 'Unknown',
    state: parts[1] || 'Unknown',
  };
}

/**
 * Estimate drive time based on distance (rough approximation)
 * Assumes average speed of 30 mph in urban areas
 */
export function estimateDriveTime(distanceMiles: number): number {
  const avgSpeedMph = 30;
  return Math.round((distanceMiles / avgSpeedMph) * 60); // minutes
}