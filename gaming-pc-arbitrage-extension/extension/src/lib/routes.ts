/**
 * Routes Helper
 * Bridge between UI and route planning logic
 */

import { getSettings } from './settings';
import { 
  nearestNeighborRoute, 
  googleMapsUrlForRoute, 
  fuelCostEstimate,
  haversineMiles,
  type LatLng,
  type RouteStop as MapsRouteStop
} from '@arbitrage/integrations/maps/route';
import safeSpots from '@/data/safespots.json';
import type { Deal } from '@/core';

export interface RouteResult {
  stops: Array<{
    dealId: string;
    title: string;
    price: number;
    address: string;
    coord: LatLng;
    safeSpotId?: string;
    safeSpotName?: string;
    safeSpotAddress?: string;
  }>;
  totalMiles: number;
  totalTime: number;
  fuelCost: number;
  mapsUrl: string;
}

/**
 * Plan optimized route for selected deals
 */
export async function planRoute(deals: Deal[]): Promise<RouteResult> {
  const settings = await getSettings();
  
  // Extract coordinates from deals
  const stops: MapsRouteStop[] = deals.map(deal => {
    // Try to geocode from city/state if no exact coords
    const coord = geocodeApproximate(
      deal.listing.location?.city,
      deal.listing.location?.state
    );
    
    return {
      id: deal.id,
      name: deal.listing.title,
      coord,
    };
  });
  
  // Get start location from settings
  const homeCoord = geocodeApproximate(
    settings.geography?.home_base?.split(',')[0]?.trim(),
    settings.geography?.home_base?.split(',')[1]?.trim()
  );
  
  // Calculate optimal route
  const { order, milesTotal } = nearestNeighborRoute(stops, homeCoord);
  
  // Build ordered stops with safe spots
  const orderedStops = order.map(dealId => {
    const deal = deals.find(d => d.id === dealId)!;
    const coord = stops.find(s => s.id === dealId)!.coord;
    
    // Find nearest safe spot
    const safeSpot = findNearestSafeSpot(coord);
    
    return {
      dealId: deal.id,
      title: deal.listing.title,
      price: deal.listing.price,
      address: formatAddress(deal.listing.location),
      coord,
      safeSpotId: safeSpot?.id,
      safeSpotName: safeSpot?.name,
      safeSpotAddress: safeSpot?.address,
    };
  });
  
  // Calculate time and cost
  const avgSpeedMph = settings.operations?.avg_pickup_speed_mph || 25;
  const totalTime = (milesTotal / avgSpeedMph) * 60; // minutes
  const fuelCost = fuelCostEstimate(
    milesTotal,
    settings.financial?.fuel_cost_per_mile || 0.15
  );
  
  // Generate Maps URL with safe spots if available
  const mapStops = orderedStops.map(stop => ({
    coord: stop.safeSpotId ? 
      safeSpots.spots.find(s => s.id === stop.safeSpotId)!.coord :
      stop.coord
  }));
  
  const mapsUrl = googleMapsUrlForRoute(mapStops, homeCoord);
  
  return {
    stops: orderedStops,
    totalMiles: milesTotal,
    totalTime,
    fuelCost,
    mapsUrl,
  };
}

/**
 * Find nearest safe meetup spot
 */
export function findNearestSafeSpot(coord: LatLng) {
  let nearest = null;
  let minDistance = Infinity;
  
  for (const spot of safeSpots.spots) {
    const distance = haversineMiles(coord, spot.coord);
    if (distance < minDistance && distance < 10) { // Within 10 miles
      minDistance = distance;
      nearest = spot;
    }
  }
  
  return nearest;
}

/**
 * Simple geocoding approximation for major cities
 */
function geocodeApproximate(city?: string, state?: string): LatLng {
  if (!city || !state) {
    return { lat: 39.7392, lng: -104.9903 }; // Default to Denver
  }
  
  // Common city coordinates
  const cities: Record<string, LatLng> = {
    'denver,co': { lat: 39.7392, lng: -104.9903 },
    'boulder,co': { lat: 40.0150, lng: -105.2705 },
    'aurora,co': { lat: 39.7294, lng: -104.8319 },
    'seattle,wa': { lat: 47.6062, lng: -122.3321 },
    'bellevue,wa': { lat: 47.6101, lng: -122.2015 },
    'portland,or': { lat: 45.5152, lng: -122.6784 },
    'sanfrancisco,ca': { lat: 37.7749, lng: -122.4194 },
    'oakland,ca': { lat: 37.8044, lng: -122.2712 },
    'losangeles,ca': { lat: 34.0522, lng: -118.2437 },
    'phoenix,az': { lat: 33.4484, lng: -112.0740 },
    'austin,tx': { lat: 30.2672, lng: -97.7431 },
  };
  
  const key = `${city.toLowerCase()},${state.toLowerCase()}`;
  return cities[key] || { lat: 39.7392, lng: -104.9903 };
}

/**
 * Format location for display
 */
function formatAddress(location?: Deal['listing']['location']): string {
  if (!location) return 'Unknown location';
  
  const parts = [];
  if (location.address) parts.push(location.address);
  if (location.city) parts.push(location.city);
  if (location.state) parts.push(location.state);
  if (location.zipCode) parts.push(location.zipCode);
  
  return parts.join(', ');
}