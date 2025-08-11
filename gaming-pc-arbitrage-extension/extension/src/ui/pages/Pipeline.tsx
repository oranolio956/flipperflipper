import React from 'react';
import { GitPullRequest } from 'lucide-react';
import { PageHeader } from '../design/components/PageHeader';
import { EmptyState } from '../design/components/EmptyState';

export function Pipeline() {
  const helpContent = (
    <div>
      <h4>Deal Pipeline</h4>
      <p>Track deals through stages from initial contact to completion.</p>
      <ul>
        <li>Organize deals by stage (New, Contacted, Negotiating, etc.)</li>
        <li>Track key metrics like FMV, target price, and ROI</li>
        <li>Set reminders and follow-up tasks</li>
        <li>Archive completed or lost deals</li>
      </ul>
    </div>
  );

  return (
    <div className="pipeline-page">
      <PageHeader
        title="Deal Pipeline"
        description="Track deals through stages"
        helpContent={helpContent}
      />
      
      <EmptyState
        icon={GitPullRequest}
        title="No active deals"
        description="Start scanning to find deals or manually add one"
        action={{
          label: 'Add Deal',
          onClick: () => console.log('Add deal')
        }}
      />
    </div>
  );
}