import React, { useEffect, useState } from 'react';
import { TrendingUp, TrendingDown, DollarSign, Package, BarChart, Percent, Scan, Handshake, MessageSquare, TrendingDown as PriceDropIcon, FileText, GitPullRequest, Cpu } from 'lucide-react';
import { cn } from '@/lib/utils';

interface DashboardStats {
  revenue: { value: number; change: number; trend: 'up' | 'down' };
  activeDeals: { value: number; change: number; trend: 'up' | 'down' };
  avgROI: { value: number; change: number; trend: 'up' | 'down' };
  hitRate: { value: number; change: number; trend: 'up' | 'down' };
}

interface RecentActivity {
  id: string;
  type: 'scan' | 'deal' | 'message' | 'price_drop';
  title: string;
  time: string;
  platform?: string;
}

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats>({
    revenue: { value: 0, change: 0, trend: 'up' },
    activeDeals: { value: 0, change: 0, trend: 'up' },
    avgROI: { value: 0, change: 0, trend: 'up' },
    hitRate: { value: 0, change: 0, trend: 'up' }
  });

  const [recentActivity, setRecentActivity] = useState<RecentActivity[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [automationEnabled, setAutomationEnabled] = useState(false);

  useEffect(() => {
    loadDashboardData();
    
    // Listen for updates
    const handleStorageChange = (changes: any) => {
      if (changes.dashboardStats || changes.recentActivity) {
        loadDashboardData();
      }
    };
    
    chrome.storage.onChanged.addListener(handleStorageChange);
    return () => chrome.storage.onChanged.removeListener(handleStorageChange);
  }, []);

  const loadDashboardData = async () => {
    try {
      const data = await chrome.storage.local.get([
        'dashboardStats',
        'recentActivity',
        'deals',
        'scannedListings',
        'settings'
      ]);

      // Calculate real stats from stored data
      if (data.deals) {
        const activeDeals = data.deals.filter((d: any) => 
          ['contacted', 'negotiating', 'meeting_scheduled'].includes(d.status)
        );
        
        const completedDeals = data.deals.filter((d: any) => 
          d.status === 'completed'
        );

        const totalRevenue = completedDeals.reduce((sum: number, d: any) => 
          sum + (d.soldPrice - d.purchasePrice), 0
        );

        const avgROI = completedDeals.length > 0
          ? completedDeals.reduce((sum: number, d: any) => 
              sum + ((d.soldPrice - d.purchasePrice) / d.purchasePrice * 100), 0
            ) / completedDeals.length
          : 0;

        const hitRate = data.scannedListings && data.scannedListings.length > 0
          ? (data.deals.length / data.scannedListings.length * 100)
          : 0;

        setStats({
          revenue: {
            value: totalRevenue,
            change: 12, // TODO: Calculate from historical data
            trend: totalRevenue > 0 ? 'up' : 'down'
          },
          activeDeals: {
            value: activeDeals.length,
            change: 5,
            trend: 'up'
          },
          avgROI: {
            value: Math.round(avgROI),
            change: 3,
            trend: avgROI > 30 ? 'up' : 'down'
          },
          hitRate: {
            value: Math.round(hitRate),
            change: 2,
            trend: hitRate > 5 ? 'up' : 'down'
          }
        });
      }

      // Set recent activity
      if (data.recentActivity) {
        setRecentActivity(data.recentActivity.slice(0, 10));
      }

      // Check automation status
      if (data.settings?.automation?.enabled) {
        setAutomationEnabled(true);
      }

      setIsLoading(false);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
      setIsLoading(false);
    }
  };

  const toggleAutomation = async () => {
    const newState = !automationEnabled;
    setAutomationEnabled(newState);
    
    chrome.runtime.sendMessage({
      action: newState ? 'MAX_AUTO_ENABLE' : 'MAX_AUTO_DISABLE'
    });
  };

  const scanCurrentTab = () => {
    chrome.runtime.sendMessage({ action: 'SCAN_CURRENT_TAB' });
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  const formatTime = (time: string) => {
    const date = new Date(time);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    
    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    return date.toLocaleDateString();
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[600px]">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-500">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <h1 data-testid="page-title" className="text-3xl font-bold text-gray-900 dark:text-white">
        Dashboard
      </h1>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <KPICard
          title="Total Revenue"
          value={formatCurrency(stats.revenue.value)}
          change={stats.revenue.change}
          trend={stats.revenue.trend}
          icon={<DollarSign className="w-5 h-5" />}
          color="green"
        />
        <KPICard
          title="Active Deals"
          value={stats.activeDeals.value.toString()}
          change={stats.activeDeals.change}
          trend={stats.activeDeals.trend}
          icon={<Package className="w-5 h-5" />}
          color="blue"
        />
        <KPICard
          title="Avg ROI"
          value={`${stats.avgROI.value}%`}
          change={stats.avgROI.change}
          trend={stats.avgROI.trend}
          icon={<BarChart className="w-5 h-5" />}
          color="purple"
        />
        <KPICard
          title="Hit Rate"
          value={`${stats.hitRate.value}%`}
          change={stats.hitRate.change}
          trend={stats.hitRate.trend}
          icon={<Percent className="w-5 h-5" />}
          color="amber"
        />
      </div>

      {/* Quick Actions */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-4">Quick Actions</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <button
            onClick={scanCurrentTab}
            className="p-4 bg-indigo-50 dark:bg-indigo-900/20 rounded-lg hover:bg-indigo-100 dark:hover:bg-indigo-900/30 transition-colors"
          >
            <Scan className="w-6 h-6 text-indigo-600 dark:text-indigo-400 mx-auto mb-2" />
            <span className="text-sm font-medium">Scan Current Page</span>
          </button>
          
          <button
            onClick={toggleAutomation}
            className={cn(
              "p-4 rounded-lg transition-colors",
              automationEnabled
                ? "bg-green-50 dark:bg-green-900/20 hover:bg-green-100 dark:hover:bg-green-900/30"
                : "bg-gray-50 dark:bg-gray-700 hover:bg-gray-100 dark:hover:bg-gray-600"
            )}
          >
            <Cpu className={cn(
              "w-6 h-6 mx-auto mb-2",
              automationEnabled
                ? "text-green-600 dark:text-green-400"
                : "text-gray-600 dark:text-gray-400"
            )} />
            <span className="text-sm font-medium">
              {automationEnabled ? 'Max Auto ON' : 'Max Auto OFF'}
            </span>
          </button>
          
          <button
            onClick={() => chrome.runtime.sendMessage({ action: 'openUrl', url: '#/pipeline' })}
            className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors"
          >
            <GitPullRequest className="w-6 h-6 text-gray-600 dark:text-gray-400 mx-auto mb-2" />
            <span className="text-sm font-medium">View Pipeline</span>
          </button>
          
          <button
            onClick={() => chrome.runtime.sendMessage({ action: 'GENERATE_REPORT' })}
            className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors"
          >
            <FileText className="w-6 h-6 text-gray-600 dark:text-gray-400 mx-auto mb-2" />
            <span className="text-sm font-medium">Generate Report</span>
          </button>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold">Recent Activity</h2>
        </div>
        <div className="divide-y divide-gray-200 dark:divide-gray-700">
          {recentActivity.length > 0 ? (
            recentActivity.map((activity) => (
              <div key={activity.id} className="p-4 hover:bg-gray-50 dark:hover:bg-gray-700/50">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <ActivityIcon type={activity.type} />
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white">
                        {activity.title}
                      </p>
                      {activity.platform && (
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          via {activity.platform}
                        </p>
                      )}
                    </div>
                  </div>
                  <span className="text-sm text-gray-500 dark:text-gray-400">
                    {formatTime(activity.time)}
                  </span>
                </div>
              </div>
            ))
          ) : (
            <div className="p-8 text-center text-gray-500">
              <p>No recent activity</p>
              <p className="text-sm mt-2">Start scanning to see activity here</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// KPI Card Component
interface KPICardProps {
  title: string;
  value: string;
  change: number;
  trend: 'up' | 'down';
  icon: React.ReactNode;
  color: 'green' | 'blue' | 'purple' | 'amber';
}

function KPICard({ title, value, change, trend, icon, color }: KPICardProps) {
  const colorClasses = {
    green: 'bg-green-50 text-green-600 dark:bg-green-900/20 dark:text-green-400',
    blue: 'bg-blue-50 text-blue-600 dark:bg-blue-900/20 dark:text-blue-400',
    purple: 'bg-purple-50 text-purple-600 dark:bg-purple-900/20 dark:text-purple-400',
    amber: 'bg-amber-50 text-amber-600 dark:bg-amber-900/20 dark:text-amber-400'
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <div className={cn("p-2 rounded-lg", colorClasses[color])}>
          {icon}
        </div>
        <div className={cn(
          "flex items-center gap-1 text-sm font-medium",
          trend === 'up' ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
        )}>
          {trend === 'up' ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
          {Math.abs(change)}%
        </div>
      </div>
      <p className="text-2xl font-bold text-gray-900 dark:text-white">{value}</p>
      <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{title}</p>
    </div>
  );
}

// Activity Icon Component
function ActivityIcon({ type }: { type: string }) {
  const icons = {
    scan: <Scan className="w-5 h-5 text-blue-500" />,
    deal: <Handshake className="w-5 h-5 text-green-500" />,
    message: <MessageSquare className="w-5 h-5 text-purple-500" />,
    price_drop: <PriceDropIcon className="w-5 h-5 text-amber-500" />
  };

  return icons[type as keyof typeof icons] || <FileText className="w-5 h-5 text-gray-500" />;
}