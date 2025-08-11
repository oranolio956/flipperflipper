import React from 'react';
import { FlaskConical } from 'lucide-react';
import { PageHeader } from '../design/components/PageHeader';
import { EmptyState } from '../design/components/EmptyState';

export function Experiments() {
  return (
    <div className="experiments-page">
      <PageHeader
        title="Experiments"
        description="A/B test results"
      />
      
      <EmptyState
        icon={FlaskConical}
        title="No experiments running"
        description="Create experiments to test different strategies"
      />
    </div>
  );
}