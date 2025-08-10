/**
 * P&L (Profit & Loss) Calculator
 * Financial metrics and reporting
 */

import type { Deal } from '../types';
import Decimal from 'decimal.js';

export interface DealPnL {
  revenue: number;
  cogs: number;        // Cost of goods sold
  fees: number;        // Platform/payment fees
  mileage: number;     // Transportation costs
  supplies: number;    // Packaging, cleaning
  taxes: number;       // Estimated taxes
  grossProfit: number;
  netProfit: number;
  marginPct: number;
  roiPct: number;
}

export interface PnLSummary {
  totalRevenue: number;
  totalCogs: number;
  totalFees: number;
  totalExpenses: number;
  grossProfit: number;
  netProfit: number;
  avgMarginPct: number;
  dealCount: number;
  avgDealSize: number;
}

export interface PnLTimeSeries {
  date: string;
  revenue: number;
  cogs: number;
  fees: number;
  expenses: number;
  netProfit: number;
  dealCount: number;
}

/**
 * Calculate P&L for a single deal
 */
export function computeDealPnL(deal: Deal): DealPnL {
  // Use Decimal for precision
  const revenue = new Decimal(deal.sellPrice || 0);
  const cogs = new Decimal(deal.purchasePrice || 0);
  
  // Platform fees (approximate)
  let feeRate = 0;
  if (deal.sellPlatform === 'facebook') feeRate = 0.05; // 5% FB Marketplace
  else if (deal.sellPlatform === 'ebay') feeRate = 0.1; // 10% eBay
  else if (deal.sellPlatform === 'offerup') feeRate = 0.099; // 9.9% OfferUp
  
  const fees = revenue.mul(feeRate);
  
  // Mileage (IRS rate $0.655/mile for 2023)
  const mileageRate = 0.655;
  const miles = deal.logistics?.totalMiles || 0;
  const mileage = new Decimal(miles).mul(mileageRate);
  
  // Supplies estimate
  const supplies = new Decimal(deal.expenses?.supplies || 5); // Default $5
  
  // Total expenses
  const totalExpenses = fees.plus(mileage).plus(supplies);
  
  // Gross profit (revenue - COGS)
  const grossProfit = revenue.minus(cogs);
  
  // Net profit (gross - all expenses)
  const netProfit = grossProfit.minus(totalExpenses);
  
  // Estimated taxes (simplified - 25% of profit)
  const taxes = netProfit.gt(0) ? netProfit.mul(0.25) : new Decimal(0);
  const netAfterTax = netProfit.minus(taxes);
  
  // Margins
  const marginPct = revenue.gt(0) 
    ? netAfterTax.div(revenue).mul(100).toNumber()
    : 0;
    
  const roiPct = cogs.gt(0)
    ? netAfterTax.div(cogs).mul(100).toNumber()
    : 0;
  
  return {
    revenue: revenue.toNumber(),
    cogs: cogs.toNumber(),
    fees: fees.toNumber(),
    mileage: mileage.toNumber(),
    supplies: supplies.toNumber(),
    taxes: taxes.toNumber(),
    grossProfit: grossProfit.toNumber(),
    netProfit: netAfterTax.toNumber(),
    marginPct: Math.round(marginPct * 10) / 10,
    roiPct: Math.round(roiPct * 10) / 10,
  };
}

/**
 * Rollup P&L for multiple deals
 */
export function rollupPnL(
  deals: Deal[],
  dateRange?: { start: Date; end: Date }
): PnLSummary {
  // Filter by date if provided
  let filteredDeals = deals;
  if (dateRange) {
    filteredDeals = deals.filter(d => {
      const soldDate = d.soldAt ? new Date(d.soldAt) : null;
      return soldDate && 
             soldDate >= dateRange.start && 
             soldDate <= dateRange.end;
    });
  }
  
  // Only include sold deals
  const soldDeals = filteredDeals.filter(d => d.stage === 'sold');
  
  if (soldDeals.length === 0) {
    return {
      totalRevenue: 0,
      totalCogs: 0,
      totalFees: 0,
      totalExpenses: 0,
      grossProfit: 0,
      netProfit: 0,
      avgMarginPct: 0,
      dealCount: 0,
      avgDealSize: 0,
    };
  }
  
  // Calculate P&L for each deal
  const pnls = soldDeals.map(d => computeDealPnL(d));
  
  // Sum up totals
  const totals = pnls.reduce((acc, pnl) => ({
    revenue: acc.revenue.plus(pnl.revenue),
    cogs: acc.cogs.plus(pnl.cogs),
    fees: acc.fees.plus(pnl.fees),
    expenses: acc.expenses.plus(pnl.mileage).plus(pnl.supplies).plus(pnl.taxes),
    grossProfit: acc.grossProfit.plus(pnl.grossProfit),
    netProfit: acc.netProfit.plus(pnl.netProfit),
  }), {
    revenue: new Decimal(0),
    cogs: new Decimal(0),
    fees: new Decimal(0),
    expenses: new Decimal(0),
    grossProfit: new Decimal(0),
    netProfit: new Decimal(0),
  });
  
  const avgMarginPct = totals.revenue.gt(0)
    ? totals.netProfit.div(totals.revenue).mul(100).toNumber()
    : 0;
  
  return {
    totalRevenue: totals.revenue.toNumber(),
    totalCogs: totals.cogs.toNumber(),
    totalFees: totals.fees.toNumber(),
    totalExpenses: totals.expenses.toNumber(),
    grossProfit: totals.grossProfit.toNumber(),
    netProfit: totals.netProfit.toNumber(),
    avgMarginPct: Math.round(avgMarginPct * 10) / 10,
    dealCount: soldDeals.length,
    avgDealSize: totals.revenue.div(soldDeals.length).toNumber(),
  };
}

/**
 * Generate time series data for charts
 */
export function generatePnLTimeSeries(
  deals: Deal[],
  granularity: 'daily' | 'weekly' | 'monthly' = 'monthly'
): PnLTimeSeries[] {
  const soldDeals = deals.filter(d => d.stage === 'sold' && d.soldAt);
  
  if (soldDeals.length === 0) return [];
  
  // Group deals by period
  const grouped = new Map<string, Deal[]>();
  
  soldDeals.forEach(deal => {
    const date = new Date(deal.soldAt!);
    let key: string;
    
    if (granularity === 'daily') {
      key = date.toISOString().split('T')[0];
    } else if (granularity === 'weekly') {
      const weekStart = new Date(date);
      weekStart.setDate(date.getDate() - date.getDay());
      key = weekStart.toISOString().split('T')[0];
    } else {
      key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
    }
    
    if (!grouped.has(key)) {
      grouped.set(key, []);
    }
    grouped.get(key)!.push(deal);
  });
  
  // Calculate P&L for each period
  const series: PnLTimeSeries[] = [];
  
  Array.from(grouped.entries())
    .sort(([a], [b]) => a.localeCompare(b))
    .forEach(([date, periodDeals]) => {
      const summary = rollupPnL(periodDeals);
      
      series.push({
        date,
        revenue: summary.totalRevenue,
        cogs: summary.totalCogs,
        fees: summary.totalFees,
        expenses: summary.totalExpenses - summary.totalFees,
        netProfit: summary.netProfit,
        dealCount: summary.dealCount,
      });
    });
  
  return series;
}

/**
 * Export P&L data as CSV
 */
export function exportPnLCsv(deals: Deal[]): string {
  const soldDeals = deals.filter(d => d.stage === 'sold');
  
  const headers = [
    'Date Sold',
    'Title',
    'Purchase Price',
    'Sell Price', 
    'Platform Fees',
    'Mileage Cost',
    'Supplies',
    'Est. Taxes',
    'Net Profit',
    'Margin %',
    'ROI %',
  ];
  
  const rows = soldDeals.map(deal => {
    const pnl = computeDealPnL(deal);
    
    return [
      deal.soldAt ? new Date(deal.soldAt).toLocaleDateString() : '',
      `"${deal.listing.title.replace(/"/g, '""')}"`,
      pnl.cogs.toFixed(2),
      pnl.revenue.toFixed(2),
      pnl.fees.toFixed(2),
      pnl.mileage.toFixed(2),
      pnl.supplies.toFixed(2),
      pnl.taxes.toFixed(2),
      pnl.netProfit.toFixed(2),
      pnl.marginPct.toFixed(1),
      pnl.roiPct.toFixed(1),
    ];
  });
  
  return [
    headers.join(','),
    ...rows.map(row => row.join(','))
  ].join('\n');
}