import React from 'react';
import { Scan } from 'lucide-react';
import { PageHeader } from '../design/components/PageHeader';
import { EmptyState } from '../design/components/EmptyState';

export function Scanner() {
  const helpContent = (
    <div>
      <h4>Scanner Overview</h4>
      <p>Scan marketplace pages to find and analyze gaming PC listings.</p>
      <ul>
        <li>Navigate to a marketplace listing page</li>
        <li>Click scan to analyze the page</li>
        <li>Review component detection and pricing</li>
        <li>Add promising deals to your pipeline</li>
      </ul>
    </div>
  );

  return (
    <div className="scanner-page">
      <PageHeader
        title="Scanner"
        description="Scan and triage marketplace listings"
        helpContent={helpContent}
      />
      
      <EmptyState
        icon={Scan}
        title="No active scan"
        description="Navigate to a marketplace listing and click scan to analyze it"
        action={{
          label: 'Go to Facebook Marketplace',
          onClick: () => window.open('https://facebook.com/marketplace', '_blank')
        }}
      />
    </div>
  );
}