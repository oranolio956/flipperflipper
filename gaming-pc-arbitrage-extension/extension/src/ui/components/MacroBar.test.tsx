/**
 * MacroBar Tests
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MacroBar } from './MacroBar';
import type { Deal } from '@/core';

// Mock dependencies
vi.mock('@/lib/hooks/useHotkeys', () => ({
  useHotkeys: vi.fn(),
}));

vi.mock('@/lib/negotiationBridge', () => ({
  generateDraft: vi.fn().mockResolvedValue({
    content: 'Test message content',
  }),
}));

vi.mock('@/lib/offerEngine', () => ({
  suggestAnchors: vi.fn().mockReturnValue({
    open: 750,
    target: 850,
    walkaway: 950,
  }),
}));

vi.mock('@/lib/calendar', () => ({
  exportDealToIcs: vi.fn().mockReturnValue('BEGIN:VCALENDAR...'),
}));

// Mock clipboard API
Object.assign(navigator, {
  clipboard: {
    writeText: vi.fn().mockResolvedValue(undefined),
  },
});

const mockDeal: Deal = {
  id: '123',
  listingId: 'listing-123',
  listing: {
    id: 'listing-123',
    title: 'Gaming PC',
    externalId: 'ext-123',
    platform: 'facebook',
    url: 'https://example.com',
    price: { amount: 1000, currency: 'USD', formatted: '$1,000' },
    seller: { id: 'seller-123', name: 'John Doe', profileUrl: '' },
    location: { city: 'SF', state: 'CA' },
    metadata: { createdAt: new Date(), updatedAt: new Date(), status: 'active' },
  },
  stage: 'negotiating',
  financials: {
    purchasePrice: 800,
    listingFees: 0,
    transportCost: 0,
    refurbCosts: [],
    totalInvestment: 800,
    estimatedResale: 1200,
    estimatedProfit: 400,
  },
  negotiation: {
    askingPrice: 1000,
    offers: [],
    walkAwayPrice: 700,
    targetPrice: 850,
  },
  communication: {
    messages: [],
    templates: [],
    sellerEngagement: 'medium',
  },
  logistics: {
    pickup: { 
      scheduled: new Date('2024-02-01T14:00:00'),
      confirmed: true, 
      notes: '' 
    },
    transport: { method: 'personal', cost: 0, distance: 10, time: 30 },
  },
  documentation: {
    receipts: [],
    photos: [],
    serialNumbers: [],
    testResults: [],
  },
  analytics: {
    daysInStage: {} as any,
    totalCycleDays: 7,
    profitMargin: 0.25,
    roi: 0.5,
    scorecard: { negotiation: 8, timing: 9, execution: 8, overall: 8 },
  },
  metadata: {
    createdAt: new Date(),
    updatedAt: new Date(),
    createdBy: 'user-123',
    tags: [],
    priority: 'medium',
    archived: false,
  },
} as Deal;

describe('MacroBar', () => {
  it('should render enabled actions', () => {
    render(<MacroBar deal={mockDeal} fmv={1000} riskScore={20} />);
    
    expect(screen.getByText('Draft Opener')).toBeInTheDocument();
    expect(screen.getByText('Follow-up 24h')).toBeInTheDocument();
    expect(screen.getByText('Price Calculator')).toBeInTheDocument();
    expect(screen.getByText('Add to Calendar')).toBeInTheDocument();
    expect(screen.getByText('Mark Acquired')).toBeInTheDocument();
  });

  it('should not show actions without required data', () => {
    render(<MacroBar />);
    
    expect(screen.queryByText('Draft Opener')).not.toBeInTheDocument();
    expect(screen.queryByText('Mark Acquired')).not.toBeInTheDocument();
  });

  it('should copy draft message to clipboard', async () => {
    const { generateDraft } = await import('@/lib/negotiationBridge');
    render(<MacroBar deal={mockDeal} />);
    
    const button = screen.getByText('Draft Opener');
    fireEvent.click(button);
    
    expect(generateDraft).toHaveBeenCalledWith(mockDeal, 'opening');
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith('Test message content');
  });

  it('should calculate and copy price anchors', async () => {
    const { suggestAnchors } = await import('@/lib/offerEngine');
    render(<MacroBar fmv={1000} riskScore={20} />);
    
    const button = screen.getByText('Price Calculator');
    fireEvent.click(button);
    
    expect(suggestAnchors).toHaveBeenCalledWith(1000, 20);
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith(
      expect.stringContaining('Opening: $750')
    );
  });

  it('should export calendar event', async () => {
    const { exportDealToIcs } = await import('@/lib/calendar');
    
    // Mock URL.createObjectURL
    global.URL.createObjectURL = vi.fn().mockReturnValue('blob:test');
    global.URL.revokeObjectURL = vi.fn();
    
    // Mock document.createElement
    const mockClick = vi.fn();
    const mockAnchor = { click: mockClick, href: '', download: '' };
    vi.spyOn(document, 'createElement').mockReturnValue(mockAnchor as any);
    
    render(<MacroBar deal={mockDeal} />);
    
    const button = screen.getByText('Add to Calendar');
    fireEvent.click(button);
    
    expect(exportDealToIcs).toHaveBeenCalledWith(mockDeal);
    expect(mockAnchor.download).toBe('pickup-Gaming-PC.ics');
    expect(mockClick).toHaveBeenCalled();
  });

  it('should show hotkey tooltips', async () => {
    render(<MacroBar deal={mockDeal} fmv={1000} />);
    
    // Hover over button to show tooltip
    const button = screen.getByText('Draft Opener');
    fireEvent.mouseEnter(button);
    
    // Tooltip should show hotkey
    expect(await screen.findByText('cmd+o')).toBeInTheDocument();
  });

  it('should disable actions during processing', async () => {
    render(<MacroBar deal={mockDeal} />);
    
    const button = screen.getByText('Draft Opener');
    fireEvent.click(button);
    
    // All buttons should be disabled while processing
    const buttons = screen.getAllByRole('button');
    buttons.forEach(btn => {
      expect(btn).toBeDisabled();
    });
  });
});