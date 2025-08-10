/**
 * Maps Route Planning
 * Local route optimization with Google Maps integration
 */

export interface LatLng {
  lat: number;
  lng: number;
}

export interface RouteStop {
  id: string;
  name: string;
  coord: LatLng;
}

/**
 * Calculate distance between two points using Haversine formula
 * @returns Distance in miles
 */
export function haversineMiles(a: LatLng, b: LatLng): number {
  const R = 3959; // Earth's radius in miles
  const dLat = toRadians(b.lat - a.lat);
  const dLng = toRadians(b.lng - a.lng);
  
  const sinDLat = Math.sin(dLat / 2);
  const sinDLng = Math.sin(dLng / 2);
  
  const h = sinDLat * sinDLat + 
            Math.cos(toRadians(a.lat)) * 
            Math.cos(toRadians(b.lat)) * 
            sinDLng * sinDLng;
            
  const c = 2 * Math.atan2(Math.sqrt(h), Math.sqrt(1 - h));
  
  return R * c;
}

/**
 * Calculate optimal route using nearest neighbor algorithm
 */
export function nearestNeighborRoute(
  stops: RouteStop[], 
  start?: LatLng
): { order: string[]; milesTotal: number } {
  if (stops.length === 0) {
    return { order: [], milesTotal: 0 };
  }
  
  if (stops.length === 1) {
    return { order: [stops[0].id], milesTotal: 0 };
  }
  
  const visited = new Set<string>();
  const order: string[] = [];
  let totalMiles = 0;
  
  // Start from provided location or first stop
  let current = start || stops[0].coord;
  
  // If starting from custom location, find nearest stop
  if (start) {
    let nearestIdx = 0;
    let minDist = Infinity;
    
    for (let i = 0; i < stops.length; i++) {
      const dist = haversineMiles(current, stops[i].coord);
      if (dist < minDist) {
        minDist = dist;
        nearestIdx = i;
      }
    }
    
    visited.add(stops[nearestIdx].id);
    order.push(stops[nearestIdx].id);
    current = stops[nearestIdx].coord;
    totalMiles += minDist;
  } else {
    visited.add(stops[0].id);
    order.push(stops[0].id);
    current = stops[0].coord;
  }
  
  // Visit remaining stops using nearest neighbor
  while (visited.size < stops.length) {
    let nearestIdx = -1;
    let minDist = Infinity;
    
    for (let i = 0; i < stops.length; i++) {
      if (visited.has(stops[i].id)) continue;
      
      const dist = haversineMiles(current, stops[i].coord);
      if (dist < minDist) {
        minDist = dist;
        nearestIdx = i;
      }
    }
    
    if (nearestIdx === -1) break;
    
    visited.add(stops[nearestIdx].id);
    order.push(stops[nearestIdx].id);
    current = stops[nearestIdx].coord;
    totalMiles += minDist;
  }
  
  return { order, milesTotal: totalMiles };
}

/**
 * Generate Google Maps URL for multi-stop route
 */
export function googleMapsUrlForRoute(
  stops: { coord: LatLng }[], 
  start?: LatLng
): string {
  if (stops.length === 0) return '';
  
  const baseUrl = 'https://www.google.com/maps/dir';
  const params: string[] = [];
  
  // Add start location if provided
  if (start) {
    params.push(`${start.lat},${start.lng}`);
  }
  
  // Add all stops
  for (const stop of stops) {
    params.push(`${stop.coord.lat},${stop.coord.lng}`);
  }
  
  return `${baseUrl}/${params.join('/')}/`;
}

/**
 * Estimate fuel cost for total miles
 */
export function fuelCostEstimate(miles: number, fuelCostPerMile: number): number {
  return Math.round(miles * fuelCostPerMile * 100) / 100;
}

/**
 * Convert degrees to radians
 */
function toRadians(degrees: number): number {
  return degrees * (Math.PI / 180);
}