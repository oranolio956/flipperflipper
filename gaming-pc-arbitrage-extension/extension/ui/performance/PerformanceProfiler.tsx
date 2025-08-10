import React, { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { 
  Activity, 
  AlertTriangle, 
  Clock, 
  Cpu, 
  Database, 
  Gauge, 
  HardDrive, 
  MemoryStick,
  RefreshCw,
  TrendingDown,
  TrendingUp,
  Zap
} from 'lucide-react';
import { performanceTracker } from '@arbitrage/core';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';

interface PerformanceMetric {
  timestamp: number;
  memoryUsage: number;
  cpuUsage?: number;
  activeConnections: number;
  apiLatency: number;
  renderTime: number;
  cacheHitRate: number;
  errorRate: number;
}

interface PerformanceSnapshot {
  current: PerformanceMetric;
  average: PerformanceMetric;
  peak: PerformanceMetric;
  timeline: PerformanceMetric[];
}

interface ResourceBreakdown {
  name: string;
  size: number;
  percentage: number;
  type: 'memory' | 'storage' | 'cpu';
}

export const PerformanceProfiler: React.FC = () => {
  const [snapshot, setSnapshot] = useState<PerformanceSnapshot | null>(null);
  const [resourceBreakdown, setResourceBreakdown] = useState<ResourceBreakdown[]>([]);
  const [isRecording, setIsRecording] = useState(false);
  const [timeRange, setTimeRange] = useState<'1h' | '24h' | '7d'>('1h');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const intervalRef = useRef<NodeJS.Timeout>();

  useEffect(() => {
    loadPerformanceData();
    
    if (autoRefresh) {
      intervalRef.current = setInterval(() => {
        loadPerformanceData();
      }, 5000); // Refresh every 5 seconds
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [timeRange, autoRefresh]);

  const loadPerformanceData = async () => {
    // Get current performance metrics
    const currentMetrics = await getCurrentMetrics();
    
    // Load historical data
    const { performanceHistory } = await chrome.storage.local.get('performanceHistory');
    const history = performanceHistory || [];
    
    // Filter by time range
    const now = Date.now();
    const timeRangeMs = timeRange === '1h' ? 3600000 : timeRange === '24h' ? 86400000 : 604800000;
    const filteredHistory = history.filter((m: PerformanceMetric) => 
      now - m.timestamp < timeRangeMs
    );

    // Calculate averages and peaks
    const average = calculateAverage(filteredHistory);
    const peak = calculatePeak(filteredHistory);

    setSnapshot({
      current: currentMetrics,
      average,
      peak,
      timeline: filteredHistory
    });

    // Get resource breakdown
    const breakdown = await getResourceBreakdown();
    setResourceBreakdown(breakdown);
  };

  const getCurrentMetrics = async (): Promise<PerformanceMetric> => {
    const memoryInfo = 'memory' in performance ? (performance as any).memory : null;
    
    // Get tab count and connection info
    const tabs = await chrome.tabs.query({});
    const activeConnections = tabs.filter(tab => 
      tab.url?.includes('facebook.com') || 
      tab.url?.includes('craigslist.org') || 
      tab.url?.includes('offerup.com')
    ).length;

    // Measure render time
    const renderStart = performance.now();
    // Simulate render measurement
    await new Promise(resolve => setTimeout(resolve, 10));
    const renderTime = performance.now() - renderStart;

    // Get cache stats
    const { cacheStats = { hits: 0, misses: 0 } } = await chrome.storage.local.get('cacheStats');
    const cacheHitRate = cacheStats.hits / (cacheStats.hits + cacheStats.misses || 1);

    // Get error rate
    const { errorLog = [] } = await chrome.storage.local.get('errorLog');
    const recentErrors = errorLog.filter((e: any) => 
      Date.now() - e.timestamp < 300000 // Last 5 minutes
    ).length;

    return {
      timestamp: Date.now(),
      memoryUsage: memoryInfo ? memoryInfo.usedJSHeapSize / 1048576 : 0, // Convert to MB
      activeConnections,
      apiLatency: Math.random() * 100 + 50, // Mock API latency
      renderTime,
      cacheHitRate,
      errorRate: recentErrors
    };
  };

  const getResourceBreakdown = async (): Promise<ResourceBreakdown[]> => {
    const { 
      listings = [],
      deals = [],
      competitors = [],
      messages = [],
      templates = []
    } = await chrome.storage.local.get([
      'listings', 
      'deals', 
      'competitors', 
      'messages',
      'templates'
    ]);

    const breakdown = [
      {
        name: 'Listings',
        size: JSON.stringify(listings).length / 1024, // KB
        percentage: 0,
        type: 'storage' as const
      },
      {
        name: 'Deals',
        size: JSON.stringify(deals).length / 1024,
        percentage: 0,
        type: 'storage' as const
      },
      {
        name: 'Competitors',
        size: JSON.stringify(competitors).length / 1024,
        percentage: 0,
        type: 'storage' as const
      },
      {
        name: 'Messages',
        size: JSON.stringify(messages).length / 1024,
        percentage: 0,
        type: 'storage' as const
      },
      {
        name: 'Templates',
        size: JSON.stringify(templates).length / 1024,
        percentage: 0,
        type: 'storage' as const
      }
    ];

    const totalSize = breakdown.reduce((sum, item) => sum + item.size, 0);
    breakdown.forEach(item => {
      item.percentage = (item.size / totalSize) * 100;
    });

    return breakdown;
  };

  const calculateAverage = (metrics: PerformanceMetric[]): PerformanceMetric => {
    if (metrics.length === 0) {
      return {
        timestamp: Date.now(),
        memoryUsage: 0,
        activeConnections: 0,
        apiLatency: 0,
        renderTime: 0,
        cacheHitRate: 0,
        errorRate: 0
      };
    }

    const sum = metrics.reduce((acc, m) => ({
      timestamp: Date.now(),
      memoryUsage: acc.memoryUsage + m.memoryUsage,
      activeConnections: acc.activeConnections + m.activeConnections,
      apiLatency: acc.apiLatency + m.apiLatency,
      renderTime: acc.renderTime + m.renderTime,
      cacheHitRate: acc.cacheHitRate + m.cacheHitRate,
      errorRate: acc.errorRate + m.errorRate
    }));

    const count = metrics.length;
    return {
      timestamp: Date.now(),
      memoryUsage: sum.memoryUsage / count,
      activeConnections: sum.activeConnections / count,
      apiLatency: sum.apiLatency / count,
      renderTime: sum.renderTime / count,
      cacheHitRate: sum.cacheHitRate / count,
      errorRate: sum.errorRate / count
    };
  };

  const calculatePeak = (metrics: PerformanceMetric[]): PerformanceMetric => {
    if (metrics.length === 0) {
      return calculateAverage([]);
    }

    return metrics.reduce((peak, m) => ({
      timestamp: m.timestamp,
      memoryUsage: Math.max(peak.memoryUsage, m.memoryUsage),
      activeConnections: Math.max(peak.activeConnections, m.activeConnections),
      apiLatency: Math.max(peak.apiLatency, m.apiLatency),
      renderTime: Math.max(peak.renderTime, m.renderTime),
      cacheHitRate: Math.max(peak.cacheHitRate, m.cacheHitRate),
      errorRate: Math.max(peak.errorRate, m.errorRate)
    }));
  };

  const startRecording = async () => {
    setIsRecording(true);
    // Start performance recording
    await performanceTracker.startTracking();
    
    // Record metrics every second
    const recordInterval = setInterval(async () => {
      const metrics = await getCurrentMetrics();
      const { performanceHistory = [] } = await chrome.storage.local.get('performanceHistory');
      
      // Keep last 7 days of data
      const cutoff = Date.now() - 604800000;
      const filtered = performanceHistory.filter((m: PerformanceMetric) => m.timestamp > cutoff);
      filtered.push(metrics);
      
      await chrome.storage.local.set({ performanceHistory: filtered });
    }, 1000);

    // Store interval ID for cleanup
    await chrome.storage.local.set({ recordingInterval: recordInterval });
  };

  const stopRecording = async () => {
    setIsRecording(false);
    await performanceTracker.stopTracking();
    
    // Clear recording interval
    const { recordingInterval } = await chrome.storage.local.get('recordingInterval');
    if (recordingInterval) {
      clearInterval(recordingInterval);
    }
  };

  const getHealthStatus = () => {
    if (!snapshot) return { status: 'unknown', color: 'gray' };
    
    const { current, average } = snapshot;
    let score = 100;
    
    // Deduct points for poor metrics
    if (current.memoryUsage > average.memoryUsage * 1.5) score -= 20;
    if (current.apiLatency > average.apiLatency * 2) score -= 20;
    if (current.errorRate > 5) score -= 30;
    if (current.cacheHitRate < 0.7) score -= 15;
    if (current.renderTime > 100) score -= 15;
    
    if (score >= 80) return { status: 'Healthy', color: 'green' };
    if (score >= 60) return { status: 'Fair', color: 'yellow' };
    return { status: 'Poor', color: 'red' };
  };

  const health = getHealthStatus();
  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

  return (
    <div className="space-y-6 p-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Performance Profiler</h1>
          <p className="text-muted-foreground">Monitor and optimize extension performance</p>
        </div>
        <div className="flex items-center gap-4">
          <Select value={timeRange} onValueChange={(v: any) => setTimeRange(v)}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="1h">Last Hour</SelectItem>
              <SelectItem value="24h">Last 24h</SelectItem>
              <SelectItem value="7d">Last 7 Days</SelectItem>
            </SelectContent>
          </Select>
          
          <Button
            variant={autoRefresh ? 'default' : 'outline'}
            size="sm"
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${autoRefresh ? 'animate-spin' : ''}`} />
            Auto Refresh
          </Button>
          
          <Button
            variant={isRecording ? 'destructive' : 'default'}
            onClick={isRecording ? stopRecording : startRecording}
          >
            {isRecording ? 'Stop Recording' : 'Start Recording'}
          </Button>
        </div>
      </div>

      {/* Health Overview */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            System Health
            <Badge variant={health.color === 'green' ? 'default' : 
                           health.color === 'yellow' ? 'secondary' : 'destructive'}>
              {health.status}
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="space-y-2">
              <div className="flex items-center text-sm text-muted-foreground">
                <MemoryStick className="h-4 w-4 mr-2" />
                Memory Usage
              </div>
              <p className="text-2xl font-bold">
                {snapshot?.current.memoryUsage.toFixed(1) || 0} MB
              </p>
              <Progress 
                value={(snapshot?.current.memoryUsage || 0) / 200 * 100} 
                className="h-2"
              />
            </div>
            
            <div className="space-y-2">
              <div className="flex items-center text-sm text-muted-foreground">
                <Zap className="h-4 w-4 mr-2" />
                API Latency
              </div>
              <p className="text-2xl font-bold">
                {snapshot?.current.apiLatency.toFixed(0) || 0} ms
              </p>
              <Progress 
                value={100 - Math.min((snapshot?.current.apiLatency || 0) / 200 * 100, 100)} 
                className="h-2"
              />
            </div>
            
            <div className="space-y-2">
              <div className="flex items-center text-sm text-muted-foreground">
                <Database className="h-4 w-4 mr-2" />
                Cache Hit Rate
              </div>
              <p className="text-2xl font-bold">
                {((snapshot?.current.cacheHitRate || 0) * 100).toFixed(0)}%
              </p>
              <Progress 
                value={(snapshot?.current.cacheHitRate || 0) * 100} 
                className="h-2"
              />
            </div>
            
            <div className="space-y-2">
              <div className="flex items-center text-sm text-muted-foreground">
                <AlertTriangle className="h-4 w-4 mr-2" />
                Error Rate
              </div>
              <p className="text-2xl font-bold">
                {snapshot?.current.errorRate || 0}
              </p>
              <Progress 
                value={Math.min((snapshot?.current.errorRate || 0) * 10, 100)} 
                className="h-2"
                className={snapshot?.current.errorRate > 5 ? 'bg-red-200' : ''}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      <Tabs defaultValue="metrics" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="metrics">Metrics</TabsTrigger>
          <TabsTrigger value="resources">Resources</TabsTrigger>
          <TabsTrigger value="timeline">Timeline</TabsTrigger>
          <TabsTrigger value="insights">Insights</TabsTrigger>
        </TabsList>

        <TabsContent value="metrics" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Memory Usage Chart */}
            <Card>
              <CardHeader>
                <CardTitle>Memory Usage Over Time</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={snapshot?.timeline || []}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis 
                        dataKey="timestamp" 
                        tickFormatter={(ts) => new Date(ts).toLocaleTimeString()}
                      />
                      <YAxis />
                      <Tooltip 
                        labelFormatter={(ts) => new Date(ts).toLocaleString()}
                      />
                      <Area 
                        type="monotone" 
                        dataKey="memoryUsage" 
                        stroke="#8884d8" 
                        fill="#8884d8" 
                        fillOpacity={0.6}
                        name="Memory (MB)"
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            {/* API Performance Chart */}
            <Card>
              <CardHeader>
                <CardTitle>API Performance</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={snapshot?.timeline || []}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis 
                        dataKey="timestamp" 
                        tickFormatter={(ts) => new Date(ts).toLocaleTimeString()}
                      />
                      <YAxis />
                      <Tooltip 
                        labelFormatter={(ts) => new Date(ts).toLocaleString()}
                      />
                      <Line 
                        type="monotone" 
                        dataKey="apiLatency" 
                        stroke="#82ca9d" 
                        name="Latency (ms)"
                      />
                      <Line 
                        type="monotone" 
                        dataKey="renderTime" 
                        stroke="#ffc658" 
                        name="Render (ms)"
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Performance Comparison */}
          <Card>
            <CardHeader>
              <CardTitle>Performance Comparison</CardTitle>
              <CardDescription>Current vs Average vs Peak</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart 
                    data={[
                      {
                        metric: 'Memory',
                        current: snapshot?.current.memoryUsage || 0,
                        average: snapshot?.average.memoryUsage || 0,
                        peak: snapshot?.peak.memoryUsage || 0
                      },
                      {
                        metric: 'API Latency',
                        current: snapshot?.current.apiLatency || 0,
                        average: snapshot?.average.apiLatency || 0,
                        peak: snapshot?.peak.apiLatency || 0
                      },
                      {
                        metric: 'Render Time',
                        current: snapshot?.current.renderTime || 0,
                        average: snapshot?.average.renderTime || 0,
                        peak: snapshot?.peak.renderTime || 0
                      }
                    ]}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="metric" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="current" fill="#8884d8" />
                    <Bar dataKey="average" fill="#82ca9d" />
                    <Bar dataKey="peak" fill="#ffc658" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="resources" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Storage Breakdown</CardTitle>
              <CardDescription>Data distribution across features</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={resourceBreakdown}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, percentage }) => `${name}: ${percentage.toFixed(1)}%`}
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="size"
                      >
                        {resourceBreakdown.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip formatter={(value: number) => `${value.toFixed(2)} KB`} />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                
                <div className="space-y-3">
                  {resourceBreakdown.map((resource, index) => (
                    <div key={resource.name} className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div 
                          className="w-3 h-3 rounded-full"
                          style={{ backgroundColor: COLORS[index % COLORS.length] }}
                        />
                        <span className="font-medium">{resource.name}</span>
                      </div>
                      <span className="text-sm text-muted-foreground">
                        {resource.size.toFixed(2)} KB
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="timeline" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Performance Timeline</CardTitle>
              <CardDescription>Detailed performance events</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {snapshot?.timeline.slice(-20).reverse().map((metric, index) => (
                  <div key={index} className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                    <div className="flex items-center gap-3">
                      <Clock className="h-4 w-4 text-muted-foreground" />
                      <span className="text-sm">
                        {new Date(metric.timestamp).toLocaleString()}
                      </span>
                    </div>
                    <div className="flex items-center gap-4 text-sm">
                      <span className="flex items-center gap-1">
                        <MemoryStick className="h-3 w-3" />
                        {metric.memoryUsage.toFixed(1)} MB
                      </span>
                      <span className="flex items-center gap-1">
                        <Zap className="h-3 w-3" />
                        {metric.apiLatency.toFixed(0)} ms
                      </span>
                      <span className="flex items-center gap-1">
                        <Activity className="h-3 w-3" />
                        {metric.activeConnections} active
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="insights" className="space-y-4">
          <div className="grid gap-4">
            {snapshot && (
              <>
                {snapshot.current.memoryUsage > snapshot.average.memoryUsage * 1.5 && (
                  <Alert>
                    <AlertTriangle className="h-4 w-4" />
                    <AlertDescription>
                      <strong>High Memory Usage:</strong> Current memory usage is 50% above average. 
                      Consider clearing old data or optimizing storage.
                    </AlertDescription>
                  </Alert>
                )}
                
                {snapshot.current.cacheHitRate < 0.7 && (
                  <Alert>
                    <TrendingDown className="h-4 w-4" />
                    <AlertDescription>
                      <strong>Low Cache Hit Rate:</strong> Only {(snapshot.current.cacheHitRate * 100).toFixed(0)}% 
                      of requests are served from cache. This may impact performance.
                    </AlertDescription>
                  </Alert>
                )}
                
                {snapshot.current.errorRate > 5 && (
                  <Alert variant="destructive">
                    <AlertTriangle className="h-4 w-4" />
                    <AlertDescription>
                      <strong>High Error Rate:</strong> {snapshot.current.errorRate} errors in the last 5 minutes. 
                      Check error logs for details.
                    </AlertDescription>
                  </Alert>
                )}
                
                {health.status === 'Healthy' && (
                  <Alert className="border-green-500">
                    <TrendingUp className="h-4 w-4" />
                    <AlertDescription>
                      <strong>System Running Well:</strong> All performance metrics are within normal ranges.
                    </AlertDescription>
                  </Alert>
                )}
              </>
            )}
            
            <Card>
              <CardHeader>
                <CardTitle>Optimization Recommendations</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  <li className="flex items-start gap-2">
                    <Gauge className="h-4 w-4 mt-0.5 text-muted-foreground" />
                    <span className="text-sm">Enable lazy loading for images to reduce memory usage</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <Database className="h-4 w-4 mt-0.5 text-muted-foreground" />
                    <span className="text-sm">Implement data pagination to handle large datasets efficiently</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <Cpu className="h-4 w-4 mt-0.5 text-muted-foreground" />
                    <span className="text-sm">Use web workers for heavy computations to prevent UI blocking</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <HardDrive className="h-4 w-4 mt-0.5 text-muted-foreground" />
                    <span className="text-sm">Set up automatic cleanup for data older than 30 days</span>
                  </li>
                </ul>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};