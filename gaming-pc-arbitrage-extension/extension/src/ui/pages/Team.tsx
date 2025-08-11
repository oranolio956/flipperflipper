import React from 'react';
import { Users } from 'lucide-react';
import { PageHeader } from '../design/components/PageHeader';
import { EmptyState } from '../design/components/EmptyState';

export function Team() {
  return (
    <div className="team-page">
      <PageHeader
        title="Team"
        description="Manage team members"
      />
      
      <EmptyState
        icon={Users}
        title="No team members"
        description="Invite team members to collaborate on deals"
      />
    </div>
  );
}