import React from 'react';
import { Package } from 'lucide-react';
import { PageHeader } from '../design/components/PageHeader';
import { EmptyState } from '../design/components/EmptyState';

export function Inventory() {
  return (
    <div className="inventory-page">
      <PageHeader
        title="Inventory"
        description="Parts and systems tracking"
      />
      
      <EmptyState
        icon={Package}
        title="No inventory items"
        description="Add items as you acquire parts and systems"
      />
    </div>
  );
}