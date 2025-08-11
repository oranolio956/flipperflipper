import React from 'react';
import { BarChart3 } from 'lucide-react';
import { PageHeader } from '../design/components/PageHeader';
import { EmptyState } from '../design/components/EmptyState';

export function Comps() {
  return (
    <div className="comps-page">
      <PageHeader
        title="Comps"
        description="Component pricing database"
      />
      
      <EmptyState
        icon={BarChart3}
        title="No component data"
        description="Component pricing data will be collected as you scan listings"
      />
    </div>
  );
}