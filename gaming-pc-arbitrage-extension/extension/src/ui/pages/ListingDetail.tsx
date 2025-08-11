import React from 'react';
import { FileText } from 'lucide-react';
import { PageHeader } from '../design/components/PageHeader';
import { Card, CardContent } from '../design/components/Card';
import { useParams } from 'react-router-dom';

export function ListingDetail() {
  const { id } = useParams();
  
  return (
    <div className="listing-detail-page">
      <PageHeader
        title="Listing Detail"
        description="Detailed analysis and actions for this listing"
      />
      
      <Card>
        <CardContent>
          <p>Listing ID: {id}</p>
          <p>Detailed listing analysis will appear here.</p>
        </CardContent>
      </Card>
    </div>
  );
}