import React, { useState, useEffect } from 'react';
import { 
  Scan, 
  Filter, 
  ExternalLink, 
  TrendingUp,
  AlertTriangle,
  DollarSign,
  Package,
  RefreshCw
} from 'lucide-react';
import { PageHeader } from '../design/components/PageHeader';
import { Card, CardHeader, CardContent } from '../design/components/Card';
import { Button } from '../design/components/Button';
import { EmptyState, LoadingState } from '../design/components/EmptyState';
import { showToast } from '../design/components/Toast';
import { formatCurrency, formatPercent } from '../lib/utils';
import { ROUTES, buildRoute } from '../router/routes';
import { Link } from 'react-router-dom';

interface ScannedListing {
  id: string;
  title: string;
  url: string;
  platform: 'facebook' | 'craigslist' | 'offerup';
  price: number;
  estimatedValue: number;
  roi: number;
  riskScore: number;
  components: string[];
  scannedAt: Date;
  imageUrl?: string;
}

export function Scanner() {
  const [loading, setLoading] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [listings, setListings] = useState<ScannedListing[]>([]);
  const [filter, setFilter] = useState<'all' | 'high-roi' | 'low-risk'>('all');
  const [selectedListings, setSelectedListings] = useState<Set<string>>(new Set());

  useEffect(() => {
    loadScannedListings();
  }, []);

  const loadScannedListings = async () => {
    setLoading(true);
    try {
      const result = await chrome.storage.local.get(['scannedListings']);
      const listings = result.scannedListings || [];
      setListings(listings.sort((a: ScannedListing, b: ScannedListing) => b.roi - a.roi));
    } catch (error) {
      console.error('Failed to load listings:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleScanPage = async () => {
    setScanning(true);
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (tab.id) {
        await chrome.tabs.sendMessage(tab.id, { action: 'scan' });
        showToast({
          type: 'success',
          title: 'Scan Complete',
          description: 'Page has been analyzed'
        });
        // Reload listings after scan
        await loadScannedListings();
      }
    } catch (error) {
      showToast({
        type: 'error',
        title: 'Scan Failed',
        description: 'Could not scan this page'
      });
    } finally {
      setScanning(false);
    }
  };

  const handleBulkOpen = () => {
    const selected = listings.filter(l => selectedListings.has(l.id));
    selected.slice(0, 5).forEach((listing, index) => {
      setTimeout(() => {
        chrome.tabs.create({ url: listing.url, active: index === 0 });
      }, index * 200);
    });
    showToast({
      type: 'info',
      title: 'Opening Listings',
      description: `Opening ${Math.min(selected.length, 5)} tabs`
    });
  };

  const getFilteredListings = () => {
    switch (filter) {
      case 'high-roi':
        return listings.filter(l => l.roi > 0.25);
      case 'low-risk':
        return listings.filter(l => l.riskScore < 0.3);
      default:
        return listings;
    }
  };

  const helpContent = (
    <div className="help-content">
      <h4>Scanner Overview</h4>
      <p>Find and analyze gaming PC listings across marketplaces.</p>
      <h4>How to use:</h4>
      <ul>
        <li>Navigate to a marketplace search results page</li>
        <li>Click "Scan Current Page" to analyze all visible listings</li>
        <li>Results are ranked by ROI potential</li>
        <li>Select multiple listings to open in tabs</li>
        <li>Click on any listing for detailed analysis</li>
      </ul>
      <h4>Filters:</h4>
      <ul>
        <li><strong>High ROI:</strong> Shows only deals with 25%+ profit potential</li>
        <li><strong>Low Risk:</strong> Shows only verified, low-risk listings</li>
      </ul>
    </div>
  );

  if (loading) {
    return <LoadingState message="Loading scanned listings..." />;
  }

  const filteredListings = getFilteredListings();

  return (
    <div className="scanner-page">
      <PageHeader
        title="Scanner"
        description="Scan and triage marketplace listings"
        helpContent={helpContent}
        actions={
          <div className="scanner-actions">
            <select 
              className="filter-select"
              value={filter}
              onChange={(e) => setFilter(e.target.value as any)}
            >
              <option value="all">All Listings</option>
              <option value="high-roi">High ROI (&gt;25%)</option>
              <option value="low-risk">Low Risk</option>
            </select>
            {selectedListings.size > 0 && (
              <Button
                variant="secondary"
                size="sm"
                onClick={handleBulkOpen}
              >
                Open {selectedListings.size} Tab{selectedListings.size > 1 ? 's' : ''}
              </Button>
            )}
            <Button
              variant="primary"
              icon={<Scan size={16} />}
              onClick={handleScanPage}
              loading={scanning}
            >
              Scan Current Page
            </Button>
          </div>
        }
      />

      {filteredListings.length === 0 ? (
        <EmptyState
          icon={Scan}
          title="No listings found"
          description="Navigate to a marketplace page and scan to find deals"
          action={{
            label: 'Go to Facebook Marketplace',
            onClick: () => window.open('https://facebook.com/marketplace/category/computers', '_blank')
          }}
          secondaryAction={{
            label: 'View Saved Searches',
            onClick: () => window.location.href = '#' + ROUTES.AUTOMATION
          }}
        />
      ) : (
        <div className="listings-grid">
          {filteredListings.map((listing) => (
            <Card 
              key={listing.id} 
              variant="bordered" 
              className="listing-card"
              interactive
            >
              <CardContent>
                <div className="listing-header">
                  <label className="checkbox-wrapper">
                    <input
                      type="checkbox"
                      checked={selectedListings.has(listing.id)}
                      onChange={(e) => {
                        const newSelected = new Set(selectedListings);
                        if (e.target.checked) {
                          newSelected.add(listing.id);
                        } else {
                          newSelected.delete(listing.id);
                        }
                        setSelectedListings(newSelected);
                      }}
                    />
                    <span className="sr-only">Select {listing.title}</span>
                  </label>
                  <div className="listing-badges">
                    <span className={`platform-badge ${listing.platform}`}>
                      {listing.platform}
                    </span>
                    {listing.roi > 0.3 && (
                      <span className="roi-badge hot">
                        🔥 Hot Deal
                      </span>
                    )}
                  </div>
                </div>

                <Link to={buildRoute(ROUTES.LISTING_DETAIL, { id: listing.id })}>
                  <h3 className="listing-title">{listing.title}</h3>
                </Link>

                <div className="listing-metrics">
                  <div className="metric-row">
                    <span className="metric-label">
                      <DollarSign size={14} />
                      Price
                    </span>
                    <span className="metric-value">{formatCurrency(listing.price)}</span>
                  </div>
                  <div className="metric-row">
                    <span className="metric-label">
                      <TrendingUp size={14} />
                      Est. Value
                    </span>
                    <span className="metric-value">{formatCurrency(listing.estimatedValue)}</span>
                  </div>
                  <div className="metric-row">
                    <span className="metric-label">
                      <Package size={14} />
                      ROI
                    </span>
                    <span className={`metric-value ${listing.roi > 0 ? 'positive' : 'negative'}`}>
                      {formatPercent(listing.roi)}
                    </span>
                  </div>
                  <div className="metric-row">
                    <span className="metric-label">
                      <AlertTriangle size={14} />
                      Risk
                    </span>
                    <span className={`risk-score risk-${listing.riskScore < 0.3 ? 'low' : listing.riskScore < 0.7 ? 'medium' : 'high'}`}>
                      {listing.riskScore < 0.3 ? 'Low' : listing.riskScore < 0.7 ? 'Medium' : 'High'}
                    </span>
                  </div>
                </div>

                <div className="listing-components">
                  {listing.components.slice(0, 3).map((component, index) => (
                    <span key={index} className="component-chip">
                      {component}
                    </span>
                  ))}
                  {listing.components.length > 3 && (
                    <span className="component-chip more">
                      +{listing.components.length - 3} more
                    </span>
                  )}
                </div>

                <div className="listing-actions">
                  <Link to={buildRoute(ROUTES.LISTING_DETAIL, { id: listing.id })}>
                    <Button variant="secondary" size="sm" fullWidth>
                      View Details
                    </Button>
                  </Link>
                  <a 
                    href={listing.url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <Button variant="ghost" size="sm" icon={<ExternalLink size={14} />}>
                      Original
                    </Button>
                  </a>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Auto-refresh indicator */}
      {listings.length > 0 && (
        <div className="scanner-footer">
          <Button variant="ghost" size="sm" icon={<RefreshCw size={14} />} onClick={loadScannedListings}>
            Refresh
          </Button>
          <span className="scan-count">
            {filteredListings.length} of {listings.length} listings shown
          </span>
        </div>
      )}
    </div>
  );
}