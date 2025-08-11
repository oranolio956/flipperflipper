export interface SavedSearch {
  id: string;
  name: string;
  url: string;
  platform: 'facebook' | 'craigslist' | 'offerup';
  enabled: boolean;
  cadenceMinutes: number; // How often to check
  filters?: {
    minPrice?: number;
    maxPrice?: number;
    maxDistance?: number;
    keywords?: string[];
  };
  createdAt: string;
  lastScanTime?: string;
  lastScanResults?: number;
}