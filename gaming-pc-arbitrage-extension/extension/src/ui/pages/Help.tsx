import React from 'react';
import { HelpCircle } from 'lucide-react';
import { PageHeader } from '../design/components/PageHeader';
import { Card, CardHeader, CardContent } from '../design/components/Card';

export function Help() {
  return (
    <div className="help-page">
      <PageHeader
        title="Help"
        description="Guides and support"
      />
      
      <Card>
        <CardHeader title="Getting Started" />
        <CardContent>
          <p>Help documentation and guides will appear here.</p>
        </CardContent>
      </Card>
    </div>
  );
}