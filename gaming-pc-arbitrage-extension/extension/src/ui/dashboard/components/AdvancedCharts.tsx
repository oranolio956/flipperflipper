/**
 * Advanced Analytics Charts
 * Recharts components for data visualization
 */

import React from 'react';
import {
  BarChart, Bar, LineChart, Line, ScatterChart, Scatter,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  Cell
} from 'recharts';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import type { 
  CohortMetrics, 
  SeasonalityFactors, 
  ElasticityResult,
  DemandScore,
  MarginTrend 
} from '@/core/analytics';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];
const WEEKDAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

interface CohortChartProps {
  data: CohortMetrics[];
}

export function CohortChart({ data }: CohortChartProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Cohort Analysis</CardTitle>
        <CardDescription>Performance by acquisition month</CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" />
            <YAxis yAxisId="left" />
            <YAxis yAxisId="right" orientation="right" />
            <Tooltip />
            <Legend />
            <Bar yAxisId="left" dataKey="acquired" fill="#8884d8" name="Acquired" />
            <Bar yAxisId="left" dataKey="sold" fill="#82ca9d" name="Sold" />
            <Line yAxisId="right" type="monotone" dataKey="avgMarginPct" stroke="#ff7300" name="Avg Margin %" />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

interface SeasonalityChartProps {
  data: SeasonalityFactors;
}

export function SeasonalityChart({ data }: SeasonalityChartProps) {
  const weekdayData = data.weekday.map((factor, i) => ({
    name: WEEKDAYS[i],
    multiplier: factor.toFixed(2),
    value: factor,
  }));

  const monthData = data.month.map((factor, i) => ({
    name: MONTHS[i],
    multiplier: factor.toFixed(2),
    value: factor,
  }));

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <Card>
        <CardHeader>
          <CardTitle>Weekday Seasonality</CardTitle>
          <CardDescription>Sales multiplier by day of week</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={weekdayData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis domain={[0, 2]} />
              <Tooltip />
              <Bar dataKey="value" fill="#8884d8">
                {weekdayData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.value > 1 ? '#00C49F' : '#FF8042'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Monthly Seasonality</CardTitle>
          <CardDescription>Sales multiplier by month</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={monthData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis domain={[0, 2]} />
              <Tooltip />
              <Bar dataKey="value" fill="#8884d8">
                {monthData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.value > 1 ? '#00C49F' : '#FF8042'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  );
}

interface ElasticityChartProps {
  data: { points: Array<{ x: number; y: number }>; result: ElasticityResult };
}

export function ElasticityChart({ data }: ElasticityChartProps) {
  const { points, result } = data;
  
  // Generate trend line
  const trendLine = points.map(p => ({
    ...p,
    trend: result.slope * p.x + result.intercept,
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle>Price Elasticity</CardTitle>
        <CardDescription>
          Discount % vs Days to Sell (R² = {result.r2.toFixed(3)})
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <ScatterChart>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="x" 
              name="Discount %" 
              tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
            />
            <YAxis dataKey="y" name="Days to Sell" />
            <Tooltip 
              formatter={(value: any, name: string) => {
                if (name === 'Discount %') return `${(value * 100).toFixed(1)}%`;
                return value;
              }}
            />
            <Scatter name="Deals" data={points} fill="#8884d8" />
            <Line 
              type="monotone" 
              dataKey="trend" 
              data={trendLine} 
              stroke="#ff7300" 
              strokeWidth={2}
              dot={false}
              name="Trend"
            />
          </ScatterChart>
        </ResponsiveContainer>
        <div className="mt-2 text-sm text-muted-foreground">
          Formula: Days = {result.slope.toFixed(1)} × Discount% + {result.intercept.toFixed(1)}
        </div>
      </CardContent>
    </Card>
  );
}

interface DemandChartProps {
  data: DemandScore[];
}

export function DemandChart({ data }: DemandChartProps) {
  const topComponents = data.slice(0, 10);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Component Demand Ranking</CardTitle>
        <CardDescription>Top 10 by velocity × margin score</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {topComponents.map((item, idx) => (
            <div key={item.component} className="flex items-center gap-2">
              <div className="w-8 text-center font-medium">{idx + 1}</div>
              <div className="flex-1">
                <div className="flex justify-between items-center">
                  <span className="font-medium">{item.component}</span>
                  <span className="text-sm text-muted-foreground">
                    Score: {item.score.toFixed(0)}
                  </span>
                </div>
                <div className="flex gap-4 text-xs text-muted-foreground">
                  <span>Velocity: {item.velocity.toFixed(2)}/mo</span>
                  <span>Avg Margin: {(item.avgMargin * 100).toFixed(1)}%</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

interface MarginTrendChartProps {
  data: MarginTrend[];
}

export function MarginTrendChart({ data }: MarginTrendChartProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Margin Trend</CardTitle>
        <CardDescription>30-day rolling average profit margin</CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="date" 
              tickFormatter={(date) => new Date(date).toLocaleDateString()}
            />
            <YAxis 
              tickFormatter={(v) => `${v}%`}
            />
            <Tooltip 
              labelFormatter={(date) => new Date(date).toLocaleDateString()}
              formatter={(value: any, name: string) => {
                if (name === 'marginPct') return `${value.toFixed(1)}%`;
                return value;
              }}
            />
            <Line 
              type="monotone" 
              dataKey="marginPct" 
              stroke="#8884d8" 
              strokeWidth={2}
              name="Margin %"
            />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}