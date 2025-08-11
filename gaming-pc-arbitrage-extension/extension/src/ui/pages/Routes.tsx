import React from 'react';
import { Route } from 'lucide-react';
import { PageHeader } from '../design/components/PageHeader';
import { EmptyState } from '../design/components/EmptyState';

export function RoutesPlanner() {
  return (
    <div className="routes-page">
      <PageHeader
        title="Routes"
        description="Multi-stop pickup planning"
      />
      
      <EmptyState
        icon={Route}
        title="No routes planned"
        description="Routes will appear here when you have multiple pickups to optimize"
      />
    </div>
  );
}