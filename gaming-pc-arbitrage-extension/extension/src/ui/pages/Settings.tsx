import React from 'react';
import { Settings as SettingsIcon } from 'lucide-react';
import { PageHeader } from '../design/components/PageHeader';
import { Card, CardHeader, CardContent } from '../design/components/Card';

export function Settings() {
  return (
    <div className="settings-page">
      <PageHeader
        title="Settings"
        description="Configure your preferences"
      />
      
      <Card>
        <CardHeader title="General Settings" />
        <CardContent>
          <p>Settings configuration will appear here.</p>
        </CardContent>
      </Card>
    </div>
  );
}