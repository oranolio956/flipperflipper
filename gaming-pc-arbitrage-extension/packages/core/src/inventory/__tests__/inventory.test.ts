/**
 * Tests for Inventory & Pipeline Management
 */

import { describe, it, expect } from 'vitest';
import {
  addInventoryItem,
  updateItemStatus,
  calculateStockLevels,
  getInventoryMetrics,
  findInventoryItems,
  suggestBundles,
  calculateRestockRecommendations,
  type InventoryItem,
} from '../inventoryManager';
import {
  buildPipeline,
  calculatePipelineMetrics,
  getStuckDeals,
  predictStageCompletion,
  generatePipelineReport,
  type StageTransitionHistory,
} from '../../pipeline/pipelineManager';
import type { Deal } from '../../types';

describe('Inventory Manager', () => {
  const mockItems: InventoryItem[] = [
    {
      id: 'INV-1',
      type: 'complete-system',
      status: 'available',
      name: 'Gaming PC - RTX 3080',
      category: 'system',
      specs: { cpu: 'i7-12700K', gpu: 'RTX 3080', ram: '32GB' },
      acquiredDate: new Date('2024-01-01'),
      acquiredFrom: { source: 'Facebook', price: 800 },
      condition: 'good',
      location: { type: 'home', bin: 'A1' },
      costs: { purchase: 800, fees: 104, total: 904 },
    },
    {
      id: 'INV-2',
      type: 'component',
      status: 'available',
      name: 'RTX 3070',
      category: 'gpu',
      specs: { model: 'RTX 3070', vram: '8GB' },
      acquiredDate: new Date('2024-01-05'),
      acquiredFrom: { source: 'Craigslist', price: 300 },
      condition: 'good',
      location: { type: 'home', bin: 'B2' },
      costs: { purchase: 300, fees: 39, total: 339 },
    },
    {
      id: 'INV-3',
      type: 'component',
      status: 'listed',
      name: '16GB DDR4 RAM',
      category: 'ram',
      specs: { capacity: '16GB', speed: '3200MHz' },
      acquiredDate: new Date('2024-01-10'),
      acquiredFrom: { source: 'OfferUp', price: 50 },
      condition: 'like-new',
      location: { type: 'home', bin: 'C1' },
      costs: { purchase: 50, fees: 6.5, total: 56.5 },
      listedOn: [{
        platform: 'Facebook',
        listingId: 'FB123',
        price: 80,
        date: new Date('2024-01-15'),
      }],
    },
  ];

  it('should add new inventory item', () => {
    const newItem = addInventoryItem({
      type: 'component',
      status: 'testing',
      name: 'Intel i5-12600K',
      category: 'cpu',
      acquiredDate: new Date(),
      acquiredFrom: { source: 'Facebook', price: 200 },
      condition: 'good',
      location: { type: 'home' },
    });
    
    expect(newItem.id).toBeTruthy();
    expect(newItem.costs.total).toBeGreaterThan(200);
    expect(newItem.costs.fees).toBeGreaterThan(0);
  });

  it('should update item status', () => {
    const updated = updateItemStatus(mockItems[0], 'listed', {
      platform: 'Facebook',
      listingId: 'FB456',
      price: 1200,
    });
    
    expect(updated.status).toBe('listed');
    expect(updated.listedOn).toHaveLength(1);
    expect(updated.listedOn![0].price).toBe(1200);
  });

  it('should calculate stock levels', () => {
    const targets = {
      system: { target: 2, reorderPoint: 1 },
      gpu: { target: 3, reorderPoint: 1 },
      ram: { target: 5, reorderPoint: 2 },
    };
    
    const levels = calculateStockLevels(mockItems, targets);
    
    const systemLevel = levels.find(l => l.category === 'system');
    expect(systemLevel?.current).toBe(1);
    expect(systemLevel?.available).toBe(1);
    expect(systemLevel?.status).toBe('low');
    
    const gpuLevel = levels.find(l => l.category === 'gpu');
    expect(gpuLevel?.available).toBe(1);
    expect(gpuLevel?.status).toBe('low');
  });

  it('should calculate inventory metrics', () => {
    const metrics = getInventoryMetrics(mockItems);
    
    expect(metrics.totalItems).toBe(3);
    expect(metrics.totalValue).toBeGreaterThan(1000);
    expect(metrics.byStatus.available).toBe(2);
    expect(metrics.byStatus.listed).toBe(1);
    expect(metrics.byCategory.system).toBe(1);
    expect(metrics.byCategory.gpu).toBe(1);
    expect(metrics.byCategory.ram).toBe(1);
  });

  it('should find items by criteria', () => {
    const available = findInventoryItems(mockItems, { status: 'available' });
    expect(available).toHaveLength(2);
    
    const components = findInventoryItems(mockItems, { type: 'component' });
    expect(components).toHaveLength(2);
    
    const highValue = findInventoryItems(mockItems, { minValue: 500 });
    expect(highValue).toHaveLength(1);
    
    const searchResults = findInventoryItems(mockItems, { search: 'RTX' });
    expect(searchResults).toHaveLength(2);
  });

  it('should suggest bundles', () => {
    const suggestions = suggestBundles(mockItems);
    
    expect(suggestions.length).toBeGreaterThan(0);
    const firstBundle = suggestions[0];
    expect(firstBundle.bundle.length).toBeGreaterThan(1);
    expect(firstBundle.totalValue).toBeGreaterThan(0);
    expect(firstBundle.compatibility).toBeTruthy();
    expect(firstBundle.reasoning).toBeTruthy();
  });

  it('should calculate restock recommendations', () => {
    const salesHistory = [
      { category: 'gpu', soldDate: new Date('2024-01-01'), price: 400 },
      { category: 'gpu', soldDate: new Date('2024-01-15'), price: 450 },
      { category: 'gpu', soldDate: new Date('2024-02-01'), price: 420 },
      { category: 'ram', soldDate: new Date('2024-01-20'), price: 80 },
    ];
    
    const recommendations = calculateRestockRecommendations(
      mockItems,
      salesHistory,
      1000
    );
    
    expect(recommendations.length).toBeGreaterThan(0);
    const gpuRec = recommendations.find(r => r.category === 'gpu');
    expect(gpuRec).toBeDefined();
    expect(gpuRec?.quantity).toBeGreaterThan(0);
    expect(gpuRec?.estimatedCost).toBeLessThan(1000);
  });
});

describe('Pipeline Manager', () => {
  const mockDeals: Deal[] = [
    {
      id: '1',
      listingId: 'L1',
      stage: 'evaluating',
      askingPrice: 1000,
      metadata: {
        createdAt: new Date('2024-01-01'),
        updatedAt: new Date('2024-01-02'),
        source: 'manual',
        version: 1,
      },
    },
    {
      id: '2',
      listingId: 'L2',
      stage: 'negotiating',
      askingPrice: 800,
      purchasePrice: 700,
      metadata: {
        createdAt: new Date('2024-01-05'),
        updatedAt: new Date('2024-01-10'),
        source: 'manual',
        version: 1,
      },
    },
    {
      id: '3',
      listingId: 'L3',
      stage: 'acquired',
      askingPrice: 600,
      purchasePrice: 500,
      metadata: {
        createdAt: new Date('2024-01-10'),
        updatedAt: new Date('2024-01-15'),
        source: 'manual',
        version: 1,
      },
    },
  ];

  const mockHistory: StageTransitionHistory[] = [
    {
      dealId: '1',
      from: 'discovered',
      to: 'evaluating',
      timestamp: new Date('2024-01-02'),
      duration: 24,
    },
    {
      dealId: '2',
      from: 'evaluating',
      to: 'negotiating',
      timestamp: new Date('2024-01-10'),
      duration: 48,
    },
  ];

  it('should build pipeline stages', () => {
    const pipeline = buildPipeline(mockDeals);
    
    expect(pipeline.length).toBeGreaterThan(0);
    
    const evaluatingStage = pipeline.find(s => s.name === 'evaluating');
    expect(evaluatingStage?.deals).toHaveLength(1);
    expect(evaluatingStage?.metrics.count).toBe(1);
    expect(evaluatingStage?.metrics.totalValue).toBe(1000);
  });

  it('should calculate pipeline metrics', () => {
    const metrics = calculatePipelineMetrics(mockDeals, mockHistory);
    
    expect(metrics.stages.length).toBeGreaterThan(0);
    expect(metrics.velocity.overall).toBeGreaterThan(0);
    expect(metrics.forecast.expectedRevenue).toBeGreaterThan(0);
    expect(metrics.forecast.expectedDeals).toBeGreaterThan(0);
  });

  it('should identify stuck deals', () => {
    const stuckDeals = getStuckDeals(mockDeals, {
      evaluating: 1, // 1 day threshold
      negotiating: 2,
    });
    
    expect(stuckDeals.length).toBeGreaterThan(0);
    const firstStuck = stuckDeals[0];
    expect(firstStuck.daysInStage).toBeGreaterThan(firstStuck.threshold);
    expect(firstStuck.priority).toBeTruthy();
  });

  it('should predict stage completion', () => {
    const prediction = predictStageCompletion(mockDeals[0], mockHistory);
    
    expect(prediction.estimatedDays).toBeGreaterThan(0);
    expect(prediction.confidence).toBeGreaterThan(0);
    expect(prediction.confidence).toBeLessThanOrEqual(1);
    expect(prediction.factors.length).toBeGreaterThan(0);
  });

  it('should generate pipeline report', () => {
    const metrics = calculatePipelineMetrics(mockDeals, mockHistory);
    const report = generatePipelineReport(metrics, {
      start: new Date('2024-01-01'),
      end: new Date('2024-01-31'),
    });
    
    expect(report.summary).toBeTruthy();
    expect(report.summary).toContain('deals');
    expect(report.summary).toContain('$');
    expect(Array.isArray(report.highlights)).toBe(true);
    expect(Array.isArray(report.concerns)).toBe(true);
    expect(Array.isArray(report.recommendations)).toBe(true);
  });

  it('should identify bottlenecks', () => {
    const metricsWithBottlenecks = calculatePipelineMetrics([
      ...mockDeals,
      ...Array(15).fill(null).map((_, i) => ({
        ...mockDeals[0],
        id: `stuck-${i}`,
        stage: 'negotiating',
      })),
    ], mockHistory);
    
    expect(metricsWithBottlenecks.bottlenecks.length).toBeGreaterThan(0);
    const highSeverity = metricsWithBottlenecks.bottlenecks.find(b => b.severity === 'high');
    expect(highSeverity).toBeDefined();
  });
});