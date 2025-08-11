import React from 'react';
import { TrendingUp } from 'lucide-react';
import { PageHeader } from '../design/components/PageHeader';
import { EmptyState } from '../design/components/EmptyState';

export function Analytics() {
  return (
    <div className="analytics-page">
      <PageHeader
        title="Analytics"
        description="Performance insights and trends"
      />
      
      <EmptyState
        icon={TrendingUp}
        title="No analytics data"
        description="Analytics will be available once you start tracking deals"
      />
    </div>
  );
}