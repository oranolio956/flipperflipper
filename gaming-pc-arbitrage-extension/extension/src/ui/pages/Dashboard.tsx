import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, 
  Package, 
  DollarSign, 
  Clock,
  AlertCircle,
  Scan,
  Plus,
  ExternalLink
} from 'lucide-react';
import { PageHeader } from '../design/components/PageHeader';
import { Card, CardHeader, CardContent } from '../design/components/Card';
import { Button } from '../design/components/Button';
import { EmptyState, LoadingState } from '../design/components/EmptyState';
import { formatCurrency, formatPercent, formatRelativeTime } from '../lib/utils';
import { ROUTES, buildRoute } from '../router/routes';
import { Link } from 'react-router-dom';

interface DashboardStats {
  revenue: { value: number; change: number };
  activeDeals: { value: number; change: number };
  avgRoi: { value: number; change: number };
  winRate: { value: number; change: number };
}

interface RecentCandidate {
  id: string;
  title: string;
  platform: string;
  price: number;
  estimatedProfit: number;
  riskScore: number;
  foundAt: Date;
}

export function Dashboard() {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [candidates, setCandidates] = useState<RecentCandidate[]>([]);
  const [automationStatus, setAutomationStatus] = useState<'active' | 'paused' | 'off'>('off');

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      // Load from chrome.storage
      const result = await chrome.storage.local.get([
        'dashboardStats',
        'recentCandidates',
        'automationEnabled'
      ]);

      setStats(result.dashboardStats || {
        revenue: { value: 0, change: 0 },
        activeDeals: { value: 0, change: 0 },
        avgRoi: { value: 0, change: 0 },
        winRate: { value: 0, change: 0 }
      });

      setCandidates(result.recentCandidates || []);
      setAutomationStatus(result.automationEnabled ? 'active' : 'off');
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleQuickScan = () => {
    // Open current tab scanner
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (tabs[0]?.id) {
        chrome.tabs.sendMessage(tabs[0].id, { action: 'scan' });
      }
    });
  };

  const helpContent = (
    <div className="help-content">
      <h4>Dashboard Overview</h4>
      <ul>
        <li>View your key performance metrics at a glance</li>
        <li>Monitor revenue, active deals, ROI, and win rate</li>
        <li>Review recently found candidates from automated scans</li>
        <li>Quick access to scanner and deal creation</li>
      </ul>
      <h4>Metrics Explained</h4>
      <ul>
        <li><strong>Revenue:</strong> Total earnings from sold PCs</li>
        <li><strong>Active Deals:</strong> Deals currently in pipeline</li>
        <li><strong>Avg ROI:</strong> Average return on investment</li>
        <li><strong>Win Rate:</strong> Percentage of deals won</li>
      </ul>
    </div>
  );

  if (loading) {
    return <LoadingState message="Loading dashboard..." />;
  }

  return (
    <div className="dashboard-page">
      <PageHeader
        title="Dashboard"
        description="Performance metrics and insights at a glance"
        helpContent={helpContent}
        actions={
          <div className="dashboard-actions">
            <Button
              variant="secondary"
              icon={<Scan size={16} />}
              onClick={handleQuickScan}
            >
              Quick Scan
            </Button>
            <Button
              variant="primary"
              icon={<Plus size={16} />}
              onClick={() => {/* Open deal modal */}}
            >
              New Deal
            </Button>
          </div>
        }
      />

      {/* KPI Cards */}
      <div className="metrics-grid">
        <Card>
          <CardContent>
            <div className="metric">
              <div className="metric-header">
                <DollarSign className="metric-icon" />
                <span className="metric-label">Total Revenue</span>
              </div>
              <div className="metric-value">
                {formatCurrency(stats?.revenue.value || 0)}
              </div>
              <div className={`metric-change ${stats?.revenue.change > 0 ? 'positive' : 'negative'}`}>
                <TrendingUp size={16} />
                {formatPercent(stats?.revenue.change || 0)}
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent>
            <div className="metric">
              <div className="metric-header">
                <Package className="metric-icon" />
                <span className="metric-label">Active Deals</span>
              </div>
              <div className="metric-value">
                {stats?.activeDeals.value || 0}
              </div>
              <div className={`metric-change ${stats?.activeDeals.change > 0 ? 'positive' : 'negative'}`}>
                <TrendingUp size={16} />
                {stats?.activeDeals.change > 0 ? '+' : ''}{stats?.activeDeals.change || 0}
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent>
            <div className="metric">
              <div className="metric-header">
                <TrendingUp className="metric-icon" />
                <span className="metric-label">Avg ROI</span>
              </div>
              <div className="metric-value">
                {formatPercent(stats?.avgRoi.value || 0, 0)}
              </div>
              <div className={`metric-change ${stats?.avgRoi.change > 0 ? 'positive' : 'negative'}`}>
                <TrendingUp size={16} />
                {stats?.avgRoi.change > 0 ? '+' : ''}{stats?.avgRoi.change}%
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent>
            <div className="metric">
              <div className="metric-header">
                <Clock className="metric-icon" />
                <span className="metric-label">Win Rate</span>
              </div>
              <div className="metric-value">
                {formatPercent(stats?.winRate.value || 0, 0)}
              </div>
              <div className={`metric-change ${stats?.winRate.change > 0 ? 'positive' : 'negative'}`}>
                <TrendingUp size={16} />
                {stats?.winRate.change > 0 ? '+' : ''}{stats?.winRate.change}%
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Automation Status Banner */}
      {automationStatus === 'active' && (
        <Card variant="elevated" className="automation-banner">
          <CardContent>
            <div className="automation-status">
              <div className="status-info">
                <span className="status-icon active">●</span>
                <span className="status-text">
                  Max Auto is active - Scanning saved searches every 30 minutes
                </span>
              </div>
              <Link to={ROUTES.AUTOMATION}>
                <Button variant="ghost" size="sm">
                  Manage
                  <ExternalLink size={14} />
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Recent Candidates */}
      <Card>
        <CardHeader
          title="Recent Candidates"
          description="Latest finds from automated scans"
          action={
            <Link to={ROUTES.SCANNER}>
              <Button variant="ghost" size="sm">
                View All
              </Button>
            </Link>
          }
        />
        <CardContent>
          {candidates.length === 0 ? (
            <EmptyState
              icon={Scan}
              title="No recent candidates"
              description="Start scanning to find profitable deals"
              action={{
                label: 'Start Scanning',
                onClick: () => window.location.href = '#' + ROUTES.SCANNER
              }}
            />
          ) : (
            <div className="candidates-list">
              {candidates.map((candidate) => (
                <Link
                  key={candidate.id}
                  to={buildRoute(ROUTES.LISTING_DETAIL, { id: candidate.id })}
                  className="candidate-item"
                >
                  <div className="candidate-info">
                    <h4 className="candidate-title">{candidate.title}</h4>
                    <div className="candidate-meta">
                      <span className="platform">{candidate.platform}</span>
                      <span className="separator">•</span>
                      <span className="time">{formatRelativeTime(candidate.foundAt)}</span>
                    </div>
                  </div>
                  <div className="candidate-metrics">
                    <div className="price">{formatCurrency(candidate.price)}</div>
                    <div className="profit positive">+{formatCurrency(candidate.estimatedProfit)}</div>
                    {candidate.riskScore > 0.7 && (
                      <AlertCircle size={16} className="risk-indicator" />
                    )}
                  </div>
                </Link>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}