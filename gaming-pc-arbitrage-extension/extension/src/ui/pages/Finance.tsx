import React from 'react';
import { DollarSign } from 'lucide-react';
import { PageHeader } from '../design/components/PageHeader';
import { EmptyState } from '../design/components/EmptyState';

export function Finance() {
  return (
    <div className="finance-page">
      <PageHeader
        title="Finance"
        description="P&L and cash flow tracking"
      />
      
      <EmptyState
        icon={DollarSign}
        title="No financial data"
        description="Financial tracking will begin when you complete your first deal"
      />
    </div>
  );
}