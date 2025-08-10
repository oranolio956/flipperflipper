/**
 * Facebook Marketplace Content Script Entry
 * Combines parser and overlay
 */

// Import parser to start watching for listings
import './listingParser';

// Import overlay app (will mount when parser creates container)
import './overlay';