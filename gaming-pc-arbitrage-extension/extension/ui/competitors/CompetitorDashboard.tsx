/**
 * Competitor Dashboard Component
 * Displays competitor tracking data and insights
 */

import React, { useState, useEffect } from 'react';
import { competitorTracker } from '@arbitrage/core';
import type { Competitor, CompetitorInsight } from '@arbitrage/core';
import { Chart, registerables } from 'chart.js';

Chart.register(...registerables);

interface CompetitorDashboardProps {
  onCompetitorSelect?: (competitor: Competitor) => void;
}

export const CompetitorDashboard: React.FC<CompetitorDashboardProps> = ({
  onCompetitorSelect
}) => {
  const [competitors, setCompetitors] = useState<Competitor[]>([]);
  const [insights, setInsights] = useState<CompetitorInsight[]>([]);
  const [selectedCompetitor, setSelectedCompetitor] = useState<Competitor | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<'threat' | 'volume' | 'price'>('threat');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      await competitorTracker.initialize();
      const allCompetitors = competitorTracker.getAllCompetitors();
      const competitorInsights = await competitorTracker.getCompetitorInsights();
      
      setCompetitors(allCompetitors);
      setInsights(competitorInsights);
      setLoading(false);
    } catch (error) {
      console.error('Failed to load competitor data:', error);
      setLoading(false);
    }
  };

  const filteredCompetitors = competitors
    .filter(c => 
      searchQuery === '' || 
      c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.platform.toLowerCase().includes(searchQuery.toLowerCase())
    )
    .sort((a, b) => {
      switch (sortBy) {
        case 'threat':
          const threatLevels = { high: 3, medium: 2, low: 1 };
          return threatLevels[b.threatLevel] - threatLevels[a.threatLevel];
        case 'volume':
          return b.metrics.activeListings - a.metrics.activeListings;
        case 'price':
          return b.metrics.avgPrice - a.metrics.avgPrice;
        default:
          return 0;
      }
    });

  const stats = competitorTracker.getCompetitorStats();

  const handleWatchCompetitor = async (competitor: Competitor) => {
    await competitorTracker.watchCompetitor(competitor.id, {
      priceDrops: true,
      newListings: true,
      soldItems: true,
      priceThreshold: 10
    });
    
    // Show confirmation
    chrome.notifications.create({
      type: 'basic',
      iconUrl: chrome.runtime.getURL('icons/icon-48.png'),
      title: 'Competitor Watch Active',
      message: `Now monitoring ${competitor.name} for changes`
    });
  };

  if (loading) {
    return (
      <div className="competitor-dashboard loading">
        <div className="spinner"></div>
        <p>Loading competitor data...</p>
      </div>
    );
  }

  return (
    <div className="competitor-dashboard">
      {/* Header */}
      <div className="dashboard-header">
        <h2>Competitor Tracking</h2>
        <div className="header-stats">
          <div className="stat">
            <span className="stat-label">Total Competitors</span>
            <span className="stat-value">{stats.totalCompetitors}</span>
          </div>
          <div className="stat">
            <span className="stat-label">Avg Listings</span>
            <span className="stat-value">{stats.avgListingsPerCompetitor.toFixed(1)}</span>
          </div>
          <div className="stat">
            <span className="stat-label">Market Coverage</span>
            <span className="stat-value">
              {(competitors.reduce((sum, c) => sum + c.metrics.activeListings, 0))} listings
            </span>
          </div>
        </div>
      </div>

      {/* Insights Section */}
      {insights.length > 0 && (
        <div className="insights-section">
          <h3>Market Insights</h3>
          <div className="insights-grid">
            {insights.map((insight, index) => (
              <div 
                key={index} 
                className={`insight-card ${insight.severity}`}
              >
                <div className="insight-header">
                  <span className="insight-type">{insight.type}</span>
                  <span className={`severity-badge ${insight.severity}`}>
                    {insight.severity}
                  </span>
                </div>
                <h4>{insight.title}</h4>
                <p>{insight.description}</p>
                {insight.actionable && insight.suggestedAction && (
                  <div className="suggested-action">
                    <strong>Action:</strong> {insight.suggestedAction}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Controls */}
      <div className="controls">
        <div className="search-box">
          <input
            type="text"
            placeholder="Search competitors..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          <span className="search-icon">🔍</span>
        </div>
        <div className="sort-controls">
          <label>Sort by:</label>
          <select value={sortBy} onChange={(e) => setSortBy(e.target.value as any)}>
            <option value="threat">Threat Level</option>
            <option value="volume">Listing Volume</option>
            <option value="price">Avg Price</option>
          </select>
        </div>
      </div>

      {/* Competitors Grid */}
      <div className="competitors-grid">
        {filteredCompetitors.map(competitor => (
          <div 
            key={competitor.id} 
            className={`competitor-card ${competitor.threatLevel}`}
            onClick={() => {
              setSelectedCompetitor(competitor);
              onCompetitorSelect?.(competitor);
            }}
          >
            <div className="competitor-header">
              <h4>{competitor.name}</h4>
              <span className={`threat-badge ${competitor.threatLevel}`}>
                {competitor.threatLevel} threat
              </span>
            </div>
            
            <div className="competitor-metrics">
              <div className="metric">
                <span className="label">Active Listings</span>
                <span className="value">{competitor.metrics.activeListings}</span>
              </div>
              <div className="metric">
                <span className="label">Avg Price</span>
                <span className="value">${competitor.metrics.avgPrice}</span>
              </div>
              <div className="metric">
                <span className="label">Sales Velocity</span>
                <span className="value">
                  {competitor.metrics.avgResponseTime 
                    ? `${competitor.metrics.avgResponseTime}d`
                    : 'N/A'}
                </span>
              </div>
            </div>

            <div className="competitor-trends">
              {competitor.metrics.priceChangeFrequency > 2 && (
                <span className="trend-badge aggressive">Aggressive Pricer</span>
              )}
              {competitor.metrics.activeListings > 8 && (
                <span className="trend-badge volume">High Volume</span>
              )}
              {competitor.metrics.avgPrice < stats.avgListingsPerCompetitor * 0.8 && (
                <span className="trend-badge undercut">Undercutting</span>
              )}
            </div>

            <div className="competitor-actions">
              <button 
                className="watch-btn"
                onClick={(e) => {
                  e.stopPropagation();
                  handleWatchCompetitor(competitor);
                }}
              >
                👁️ Watch
              </button>
              <button 
                className="profile-btn"
                onClick={(e) => {
                  e.stopPropagation();
                  if (competitor.profileUrl) {
                    chrome.tabs.create({ url: competitor.profileUrl });
                  }
                }}
              >
                🔗 Profile
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Competitor Detail Modal */}
      {selectedCompetitor && (
        <div className="modal-overlay" onClick={() => setSelectedCompetitor(null)}>
          <div className="competitor-detail" onClick={(e) => e.stopPropagation()}>
            <div className="detail-header">
              <h3>{selectedCompetitor.name}</h3>
              <button 
                className="close-btn"
                onClick={() => setSelectedCompetitor(null)}
              >
                ×
              </button>
            </div>

            <div className="detail-content">
              <div className="detail-section">
                <h4>Metrics Overview</h4>
                <div className="metrics-detail">
                  <div className="metric-row">
                    <span>Total Listings:</span>
                    <strong>{selectedCompetitor.metrics.totalListings}</strong>
                  </div>
                  <div className="metric-row">
                    <span>Active Listings:</span>
                    <strong>{selectedCompetitor.metrics.activeListings}</strong>
                  </div>
                  <div className="metric-row">
                    <span>Sales Volume:</span>
                    <strong>{selectedCompetitor.metrics.salesVolume || 0}</strong>
                  </div>
                  <div className="metric-row">
                    <span>Avg Days to Sell:</span>
                    <strong>
                      {selectedCompetitor.metrics.avgResponseTime || 'N/A'}
                    </strong>
                  </div>
                  <div className="metric-row">
                    <span>Price Changes/Listing:</span>
                    <strong>
                      {selectedCompetitor.metrics.priceChangeFrequency.toFixed(1)}
                    </strong>
                  </div>
                </div>
              </div>

              <div className="detail-section">
                <h4>Active Listings</h4>
                <div className="listings-list">
                  {selectedCompetitor.listings
                    .filter(l => !l.soldAt)
                    .slice(0, 5)
                    .map(listing => (
                      <div key={listing.id} className="listing-item">
                        <span className="listing-title">{listing.title}</span>
                        <span className="listing-price">${listing.price}</span>
                        {listing.priceChanges.length > 0 && (
                          <span className="price-changes">
                            {listing.priceChanges.length} changes
                          </span>
                        )}
                      </div>
                    ))}
                </div>
              </div>

              <div className="detail-section">
                <h4>Price History</h4>
                <div className="price-chart-container">
                  <canvas id="price-history-chart"></canvas>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      <style jsx>{`
        .competitor-dashboard {
          padding: 20px;
          max-width: 1400px;
          margin: 0 auto;
        }

        .dashboard-header {
          margin-bottom: 30px;
        }

        .dashboard-header h2 {
          font-size: 28px;
          margin-bottom: 20px;
        }

        .header-stats {
          display: flex;
          gap: 30px;
        }

        .stat {
          background: #f5f5f5;
          padding: 15px 25px;
          border-radius: 8px;
        }

        .stat-label {
          display: block;
          font-size: 12px;
          color: #666;
          margin-bottom: 5px;
        }

        .stat-value {
          display: block;
          font-size: 24px;
          font-weight: 600;
          color: #333;
        }

        .insights-section {
          margin-bottom: 30px;
        }

        .insights-section h3 {
          font-size: 20px;
          margin-bottom: 15px;
        }

        .insights-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
          gap: 20px;
        }

        .insight-card {
          background: white;
          border: 2px solid #e0e0e0;
          border-radius: 8px;
          padding: 20px;
          transition: all 0.2s;
        }

        .insight-card.alert {
          border-color: #f44336;
          background: #fff5f5;
        }

        .insight-card.warning {
          border-color: #ff9800;
          background: #fff8f0;
        }

        .insight-card.info {
          border-color: #2196f3;
          background: #f0f8ff;
        }

        .insight-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 10px;
        }

        .insight-type {
          font-size: 12px;
          text-transform: uppercase;
          color: #666;
        }

        .severity-badge {
          font-size: 11px;
          padding: 3px 8px;
          border-radius: 12px;
          text-transform: uppercase;
        }

        .severity-badge.alert {
          background: #f44336;
          color: white;
        }

        .severity-badge.warning {
          background: #ff9800;
          color: white;
        }

        .severity-badge.info {
          background: #2196f3;
          color: white;
        }

        .insight-card h4 {
          margin: 0 0 10px 0;
          font-size: 16px;
        }

        .insight-card p {
          margin: 0 0 10px 0;
          color: #666;
          font-size: 14px;
        }

        .suggested-action {
          background: rgba(0,0,0,0.05);
          padding: 10px;
          border-radius: 4px;
          font-size: 13px;
        }

        .controls {
          display: flex;
          gap: 20px;
          margin-bottom: 20px;
        }

        .search-box {
          position: relative;
          flex: 1;
          max-width: 400px;
        }

        .search-box input {
          width: 100%;
          padding: 10px 40px 10px 15px;
          border: 1px solid #ddd;
          border-radius: 6px;
          font-size: 14px;
        }

        .search-icon {
          position: absolute;
          right: 15px;
          top: 50%;
          transform: translateY(-50%);
        }

        .sort-controls {
          display: flex;
          align-items: center;
          gap: 10px;
        }

        .sort-controls label {
          font-size: 14px;
          color: #666;
        }

        .sort-controls select {
          padding: 8px 12px;
          border: 1px solid #ddd;
          border-radius: 6px;
          font-size: 14px;
        }

        .competitors-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
          gap: 20px;
        }

        .competitor-card {
          background: white;
          border: 2px solid #e0e0e0;
          border-radius: 12px;
          padding: 20px;
          cursor: pointer;
          transition: all 0.2s;
        }

        .competitor-card:hover {
          transform: translateY(-2px);
          box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }

        .competitor-card.high {
          border-color: #f44336;
        }

        .competitor-card.medium {
          border-color: #ff9800;
        }

        .competitor-card.low {
          border-color: #4caf50;
        }

        .competitor-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 15px;
        }

        .competitor-header h4 {
          margin: 0;
          font-size: 18px;
        }

        .threat-badge {
          font-size: 12px;
          padding: 4px 10px;
          border-radius: 15px;
          text-transform: uppercase;
        }

        .threat-badge.high {
          background: #f44336;
          color: white;
        }

        .threat-badge.medium {
          background: #ff9800;
          color: white;
        }

        .threat-badge.low {
          background: #4caf50;
          color: white;
        }

        .competitor-metrics {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 15px;
          margin-bottom: 15px;
        }

        .metric {
          text-align: center;
        }

        .metric .label {
          display: block;
          font-size: 12px;
          color: #666;
          margin-bottom: 5px;
        }

        .metric .value {
          display: block;
          font-size: 18px;
          font-weight: 600;
          color: #333;
        }

        .competitor-trends {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
          margin-bottom: 15px;
        }

        .trend-badge {
          font-size: 11px;
          padding: 3px 8px;
          border-radius: 12px;
          background: #e0e0e0;
        }

        .trend-badge.aggressive {
          background: #ffebee;
          color: #c62828;
        }

        .trend-badge.volume {
          background: #e3f2fd;
          color: #1565c0;
        }

        .trend-badge.undercut {
          background: #fff3e0;
          color: #e65100;
        }

        .competitor-actions {
          display: flex;
          gap: 10px;
        }

        .watch-btn, .profile-btn {
          flex: 1;
          padding: 8px 15px;
          border: none;
          border-radius: 6px;
          font-size: 14px;
          cursor: pointer;
          transition: all 0.2s;
        }

        .watch-btn {
          background: #2196f3;
          color: white;
        }

        .watch-btn:hover {
          background: #1976d2;
        }

        .profile-btn {
          background: #f5f5f5;
          color: #333;
        }

        .profile-btn:hover {
          background: #e0e0e0;
        }

        .modal-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0,0,0,0.5);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
        }

        .competitor-detail {
          background: white;
          border-radius: 12px;
          width: 90%;
          max-width: 700px;
          max-height: 80vh;
          overflow-y: auto;
          box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }

        .detail-header {
          padding: 20px;
          border-bottom: 1px solid #e0e0e0;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .detail-header h3 {
          margin: 0;
          font-size: 24px;
        }

        .close-btn {
          background: none;
          border: none;
          font-size: 24px;
          cursor: pointer;
          width: 40px;
          height: 40px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 4px;
        }

        .close-btn:hover {
          background: #f5f5f5;
        }

        .detail-content {
          padding: 20px;
        }

        .detail-section {
          margin-bottom: 30px;
        }

        .detail-section h4 {
          font-size: 18px;
          margin-bottom: 15px;
        }

        .metrics-detail {
          background: #f5f5f5;
          padding: 15px;
          border-radius: 8px;
        }

        .metric-row {
          display: flex;
          justify-content: space-between;
          padding: 8px 0;
          border-bottom: 1px solid #e0e0e0;
        }

        .metric-row:last-child {
          border-bottom: none;
        }

        .listings-list {
          display: flex;
          flex-direction: column;
          gap: 10px;
        }

        .listing-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 12px;
          background: #f9f9f9;
          border-radius: 6px;
        }

        .listing-title {
          flex: 1;
          font-size: 14px;
        }

        .listing-price {
          font-weight: 600;
          color: #2196f3;
          margin: 0 15px;
        }

        .price-changes {
          font-size: 12px;
          color: #666;
        }

        .price-chart-container {
          height: 300px;
          padding: 20px;
          background: #f5f5f5;
          border-radius: 8px;
        }

        .loading {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          min-height: 400px;
        }

        .spinner {
          width: 48px;
          height: 48px;
          border: 4px solid #f3f3f3;
          border-top: 4px solid #2196f3;
          border-radius: 50%;
          animation: spin 1s linear infinite;
          margin-bottom: 20px;
        }

        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};