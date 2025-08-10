/**
 * Section Component - Reusable section wrapper for settings
 */

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

interface SectionProps {
  title: string;
  description?: string;
  children: React.ReactNode;
}

export function Section({ title, description, children }: SectionProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        {description && <CardDescription>{description}</CardDescription>}
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {children}
        </div>
      </CardContent>
    </Card>
  );
}