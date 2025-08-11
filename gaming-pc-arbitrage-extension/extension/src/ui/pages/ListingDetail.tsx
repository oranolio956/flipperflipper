import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { 
  FileText, 
  DollarSign, 
  TrendingUp, 
  AlertTriangle,
  Copy,
  ExternalLink,
  MessageSquare,
  Calendar,
  MapPin,
  Eye,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import { PageHeader } from '../design/components/PageHeader';
import { Card, CardHeader, CardContent } from '../design/components/Card';
import { Button } from '../design/components/Button';
import { LoadingState } from '../design/components/EmptyState';
import { showToast } from '../design/components/Toast';
import { formatCurrency, formatPercent } from '../lib/utils';
import { ROUTES } from '../router/routes';

interface ListingData {
  id: string;
  title: string;
  description: string;
  url: string;
  platform: 'facebook' | 'craigslist' | 'offerup';
  price: number;
  estimatedValue: number;
  roi: number;
  riskScore: number;
  components: Array<{
    type: string;
    model: string;
    value: number;
  }>;
  images: string[];
  location: string;
  postedDate: Date;
  sellerInfo: {
    name: string;
    responseTime?: string;
    listingsCount?: number;
  };
  analysis: {
    fmv: number;
    targetPrice: number;
    walkAwayPrice: number;
    profitMargin: number;
    confidence: number;
  };
  risks: string[];
}

export function ListingDetail() {
  const { id } = useParams();
  const [loading, setLoading] = useState(true);
  const [listing, setListing] = useState<ListingData | null>(null);
  const [offerTone, setOfferTone] = useState<'friendly' | 'professional' | 'urgent'>('friendly');
  const [offerDraft, setOfferDraft] = useState('');
  const [showComponents, setShowComponents] = useState(true);
  const [showRisks, setShowRisks] = useState(false);

  useEffect(() => {
    loadListingDetails();
  }, [id]);

  const loadListingDetails = async () => {
    setLoading(true);
    try {
      // Fetch from chrome storage - real data from scanner
      const result = await chrome.storage.local.get(['scannedListings', 'listingAnalysis']);
      const listings = result.scannedListings || [];
      const analyses = result.listingAnalysis || {};
      
      const foundListing = listings.find((l: any) => l.id === id);
      if (!foundListing) {
        setListing(null);
        return;
      }
      
      // Get or compute analysis
      let analysis = analyses[id];
      if (!analysis) {
        // Compute real-time analysis
        const componentsTotal = foundListing.components?.reduce((sum: number, c: any) => sum + (c.value || 0), 0) || 0;
        const estimatedValue = componentsTotal * 1.1; // 10% markup for assembled system
        const roi = (estimatedValue - foundListing.price) / foundListing.price;
        
        analysis = {
          fmv: estimatedValue,
          targetPrice: foundListing.price * 0.85, // Target 15% below asking
          walkAwayPrice: foundListing.price * 0.95, // Walk away at 5% below asking
          profitMargin: roi,
          confidence: roi > 0.3 ? 0.85 : 0.6
        };
        
        // Save analysis
        await chrome.storage.local.set({
          listingAnalysis: { ...analyses, [id]: analysis }
        });
      }
      
      // Compute risk factors
      const risks = [];
      if (!foundListing.images || foundListing.images.length < 3) {
        risks.push('Limited photos provided');
      }
      if (foundListing.description && foundListing.description.length < 100) {
        risks.push('Minimal description');
      }
      if (foundListing.price < estimatedValue * 0.5) {
        risks.push('Price significantly below market');
      }
      if (!foundListing.sellerInfo?.responseTime) {
        risks.push('Unknown seller response time');
      }
      
      const listingData: ListingData = {
        ...foundListing,
        estimatedValue,
        roi,
        analysis,
        risks
      };
      
      setListing(listingData);
      generateOfferDraft(listingData);
    } catch (error) {
      console.error('Failed to load listing:', error);
    } finally {
      setLoading(false);
    }
  };

  const generateOfferDraft = (listing: ListingData) => {
    const tones = {
      friendly: `Hi! I'm interested in your ${listing.title}. It looks great! I was wondering if you'd consider $${listing.analysis.targetPrice}? I can pick up today with cash in hand. Thanks!`,
      professional: `Hello, I'm interested in purchasing your gaming PC. Based on current market values, I'd like to offer $${listing.analysis.targetPrice}. I'm a serious buyer with cash ready and can arrange pickup at your convenience. Please let me know if this works for you.`,
      urgent: `Hi there! I need a gaming PC ASAP and yours is perfect. I can offer $${listing.analysis.targetPrice} cash and pick up within the hour if that works? Let me know!`
    };
    
    setOfferDraft(tones[offerTone]);
  };

  const handleCopyOffer = () => {
    navigator.clipboard.writeText(offerDraft);
    showToast({
      type: 'success',
      title: 'Copied to clipboard',
      description: 'Offer message ready to paste'
    });
  };

  const handleOpenCompose = () => {
    // Open the marketplace messaging in new tab
    if (listing) {
      chrome.tabs.create({ url: listing.url });
      showToast({
        type: 'info',
        title: 'Opening listing',
        description: 'Paste your message and send manually'
      });
    }
  };

  const helpContent = (
    <div className="help-content">
      <h4>Listing Analysis</h4>
      <p>Review detailed component breakdown, pricing analysis, and risk assessment.</p>
      <h4>Offer Builder:</h4>
      <ul>
        <li>Select your preferred tone</li>
        <li>Review the generated message</li>
        <li>Copy and manually send (no auto-send per ToS)</li>
      </ul>
      <h4>Next Best Actions:</h4>
      <p>Follow suggested steps to maximize success rate</p>
    </div>
  );

  if (loading) {
    return <LoadingState message="Loading listing details..." />;
  }

  if (!listing) {
    return (
      <div className="listing-detail-page">
        <PageHeader title="Listing Not Found" description="This listing could not be loaded" />
      </div>
    );
  }

  return (
    <div className="listing-detail-page">
      <PageHeader
        title={listing.title}
        description={`Listed ${formatRelativeTime(listing.postedDate)} on ${listing.platform}`}
        helpContent={helpContent}
        actions={
          <div className="listing-actions">
            <a href={listing.url} target="_blank" rel="noopener noreferrer">
              <Button variant="secondary" icon={<ExternalLink size={16} />}>
                View Original
              </Button>
            </a>
            <Button variant="primary" icon={<MessageSquare size={16} />} onClick={handleOpenCompose}>
              Make Offer
            </Button>
          </div>
        }
      />

      <div className="listing-layout">
        {/* Main Column */}
        <div className="listing-main">
          {/* Pricing Analysis */}
          <Card variant="elevated">
            <CardHeader title="Pricing Analysis" />
            <CardContent>
              <div className="pricing-grid">
                <div className="price-stat">
                  <label>Asking Price</label>
                  <span className="value">{formatCurrency(listing.price)}</span>
                </div>
                <div className="price-stat">
                  <label>Fair Market Value</label>
                  <span className="value">{formatCurrency(listing.analysis.fmv)}</span>
                </div>
                <div className="price-stat">
                  <label>Target Price</label>
                  <span className="value highlight">{formatCurrency(listing.analysis.targetPrice)}</span>
                </div>
                <div className="price-stat">
                  <label>Walk-away Price</label>
                  <span className="value">{formatCurrency(listing.analysis.walkAwayPrice)}</span>
                </div>
              </div>
              
              <div className="roi-display">
                <div className="roi-bar">
                  <div 
                    className="roi-fill"
                    style={{ width: `${Math.min(listing.roi * 100, 100)}%` }}
                  />
                </div>
                <div className="roi-stats">
                  <span>ROI: {formatPercent(listing.roi)}</span>
                  <span>Profit Margin: {formatPercent(listing.analysis.profitMargin)}</span>
                  <span>Confidence: {formatPercent(listing.analysis.confidence)}</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Component Breakdown */}
          <Card>
            <CardHeader 
              title="Component Breakdown"
              action={
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowComponents(!showComponents)}
                  icon={showComponents ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                />
              }
            />
            {showComponents && (
              <CardContent>
                <div className="components-table">
                  {listing.components.map((component, index) => (
                    <div key={index} className="component-row">
                      <span className="component-type">{component.type}</span>
                      <span className="component-model">{component.model}</span>
                      <span className="component-value">{formatCurrency(component.value)}</span>
                    </div>
                  ))}
                  <div className="component-row total">
                    <span className="component-type">Total Value</span>
                    <span className="component-model"></span>
                    <span className="component-value">{formatCurrency(listing.estimatedValue)}</span>
                  </div>
                </div>
              </CardContent>
            )}
          </Card>

          {/* Risk Assessment */}
          <Card variant={listing.riskScore > 0.5 ? 'bordered' : 'default'}>
            <CardHeader 
              title="Risk Assessment"
              action={
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowRisks(!showRisks)}
                  icon={showRisks ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                />
              }
            />
            {showRisks && (
              <CardContent>
                <div className={`risk-level risk-${listing.riskScore < 0.3 ? 'low' : listing.riskScore < 0.7 ? 'medium' : 'high'}`}>
                  <AlertTriangle size={20} />
                  <span>Risk Level: {listing.riskScore < 0.3 ? 'Low' : listing.riskScore < 0.7 ? 'Medium' : 'High'}</span>
                </div>
                {listing.risks.length > 0 && (
                  <ul className="risk-list">
                    {listing.risks.map((risk, index) => (
                      <li key={index}>{risk}</li>
                    ))}
                  </ul>
                )}
              </CardContent>
            )}
          </Card>
        </div>

        {/* Sidebar */}
        <div className="listing-sidebar">
          {/* Offer Builder */}
          <Card variant="elevated">
            <CardHeader 
              title="Offer Builder" 
              description="Draft your message (manual send required)"
            />
            <CardContent>
              <div className="offer-controls">
                <label>Tone</label>
                <select 
                  value={offerTone}
                  onChange={(e) => {
                    setOfferTone(e.target.value as any);
                    generateOfferDraft(listing);
                  }}
                >
                  <option value="friendly">Friendly</option>
                  <option value="professional">Professional</option>
                  <option value="urgent">Urgent Buyer</option>
                </select>
              </div>
              
              <textarea
                className="offer-draft"
                value={offerDraft}
                onChange={(e) => setOfferDraft(e.target.value)}
                rows={6}
              />
              
              <div className="offer-actions">
                <Button 
                  variant="secondary" 
                  fullWidth 
                  icon={<Copy size={16} />}
                  onClick={handleCopyOffer}
                >
                  Copy Message
                </Button>
                <Button 
                  variant="primary" 
                  fullWidth
                  icon={<MessageSquare size={16} />}
                  onClick={handleOpenCompose}
                >
                  Open Compose
                </Button>
              </div>
              
              <p className="compliance-note">
                <AlertTriangle size={14} />
                Platform rules require manual message sending
              </p>
            </CardContent>
          </Card>

          {/* Next Best Action */}
          <Card>
            <CardHeader title="Next Best Action" />
            <CardContent>
              <div className="actions-list">
                <button className="action-item">
                  <Calendar size={16} />
                  <span>Schedule follow-up for tomorrow</span>
                </button>
                <button className="action-item">
                  <MapPin size={16} />
                  <span>Add to pickup route</span>
                </button>
                <button className="action-item">
                  <Eye size={16} />
                  <span>Watch for price drops</span>
                </button>
                <Link to={ROUTES.COMPS} className="action-item">
                  <TrendingUp size={16} />
                  <span>Update component prices</span>
                </Link>
              </div>
            </CardContent>
          </Card>

          {/* Seller Info */}
          <Card>
            <CardHeader title="Seller Information" />
            <CardContent>
              <div className="seller-info">
                <div className="info-row">
                  <span className="label">Name</span>
                  <span className="value">{listing.sellerInfo.name}</span>
                </div>
                <div className="info-row">
                  <span className="label">Response Time</span>
                  <span className="value">{listing.sellerInfo.responseTime}</span>
                </div>
                <div className="info-row">
                  <span className="label">Other Listings</span>
                  <span className="value">{listing.sellerInfo.listingsCount}</span>
                </div>
                <div className="info-row">
                  <span className="label">Location</span>
                  <span className="value">{listing.location}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

// Helper function
function formatRelativeTime(date: Date): string {
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  
  if (diffDays === 0) return 'today';
  if (diffDays === 1) return 'yesterday';
  if (diffDays < 7) return `${diffDays} days ago`;
  return date.toLocaleDateString();
}