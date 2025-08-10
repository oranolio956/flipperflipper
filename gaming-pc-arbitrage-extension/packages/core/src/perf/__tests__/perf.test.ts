/**
 * Tests for Performance Modules
 */

import { describe, it, expect } from 'vitest';
import {
  predictBenchmarkScore,
  getPerformanceTier,
  compareToBenchmarks,
} from '../benchPredictor';
import { detectBottlenecks } from '../bottleneck';

describe('Benchmark Predictor', () => {
  it('should predict high-end system score', () => {
    const score = predictBenchmarkScore({
      cpu: 'Intel i9-12900K',
      gpu: 'RTX 4090',
      ram: { capacity: 32, speed: 3600 },
      storage: [
        { type: 'nvme', capacity: 1024 },
        { type: 'ssd', capacity: 2048 },
      ],
    });
    
    expect(score.overall).toBeGreaterThan(850);
    expect(score.gaming).toBeGreaterThan(900);
    expect(score.confidence).toBe('high');
    expect(score.breakdown.gpu).toBeGreaterThan(90);
  });

  it('should predict mid-range system score', () => {
    const score = predictBenchmarkScore({
      cpu: 'Intel i5-12400',
      gpu: 'RTX 3060',
      ram: { capacity: 16, speed: 3200 },
      storage: [{ type: 'ssd', capacity: 512 }],
    });
    
    expect(score.overall).toBeGreaterThan(400);
    expect(score.overall).toBeLessThan(700);
    expect(score.gaming).toBeLessThan(score.productivity * 1.2);
  });

  it('should handle missing components', () => {
    const score = predictBenchmarkScore({
      gpu: 'RTX 3070',
      ram: { capacity: 16 },
    });
    
    expect(score.confidence).toBe('medium');
    expect(score.breakdown.cpu).toBe(50); // Default
  });

  it('should calculate performance tier', () => {
    const enthusiast = getPerformanceTier(900);
    expect(enthusiast.tier).toBe('Enthusiast');
    expect(enthusiast.description).toContain('4K');
    
    const midRange = getPerformanceTier(550);
    expect(midRange.tier).toBe('Mid-Range');
    expect(midRange.description).toContain('1080p');
  });

  it('should estimate FPS from benchmark score', () => {
    const benchmarks = compareToBenchmarks(700);
    
    expect(benchmarks.fps1080p.low).toBeGreaterThan(90);
    expect(benchmarks.fps1440p.low).toBeGreaterThan(60);
    expect(benchmarks.renderTime).toBeLessThan(20);
  });

  it('should score RAM correctly', () => {
    const score1 = predictBenchmarkScore({
      ram: { capacity: 8, speed: 2666 },
    });
    
    const score2 = predictBenchmarkScore({
      ram: { capacity: 32, speed: 3600 },
    });
    
    expect(score2.breakdown.ram).toBeGreaterThan(score1.breakdown.ram + 20);
  });
});

describe('Bottleneck Detector', () => {
  it('should detect CPU bottleneck with high-end GPU', () => {
    const analysis = detectBottlenecks({
      cpu: { model: 'Intel i3-10100' },
      gpu: { model: 'RTX 3080', tier: 'A' },
      ram: { capacity: 16 },
      storage: [{ type: 'ssd', capacity: 512 }],
    });
    
    expect(analysis.primary?.component).toBe('cpu');
    expect(analysis.primary?.severity).toBe('severe');
    expect(analysis.recommendations[0]).toContain('Upgrade to');
  });

  it('should detect RAM bottleneck', () => {
    const analysis = detectBottlenecks({
      cpu: { model: 'Intel i7-12700K' },
      gpu: { model: 'RTX 3080', tier: 'A' },
      ram: { capacity: 8, speed: 2666, channels: 1 },
      storage: [{ type: 'nvme', capacity: 1024 }],
    });
    
    expect(analysis.primary?.component).toBe('ram');
    expect(analysis.recommendations.some(r => r.includes('16GB'))).toBe(true);
  });

  it('should detect storage bottleneck', () => {
    const analysis = detectBottlenecks({
      cpu: { model: 'Intel i5-12600K' },
      gpu: { model: 'RTX 3070' },
      ram: { capacity: 16 },
      storage: [{ type: 'hdd', capacity: 1000 }],
    });
    
    expect(analysis.primary?.component).toBe('storage');
    expect(analysis.primary?.severity).toBe('severe');
    expect(analysis.recommendations[0]).toContain('SSD');
  });

  it('should detect VRAM bottleneck', () => {
    const analysis = detectBottlenecks({
      gpu: { model: 'GTX 1060', vram: 3 },
      ram: { capacity: 16 },
    });
    
    const vramBottleneck = analysis.primary || analysis.secondary;
    expect(vramBottleneck?.reason).toContain('VRAM');
    expect(vramBottleneck?.severity).toBe('severe');
  });

  it('should detect balanced system', () => {
    const analysis = detectBottlenecks({
      cpu: { model: 'Intel i5-12600K' },
      gpu: { model: 'RTX 3060 Ti', tier: 'B' },
      ram: { capacity: 16, speed: 3200, channels: 2 },
      storage: [
        { type: 'nvme', capacity: 512 },
        { type: 'ssd', capacity: 1000 },
      ],
    });
    
    expect(analysis.balanced).toBe(true);
    expect(analysis.recommendations[0]).toContain('well-balanced');
  });

  it('should detect single channel RAM bottleneck', () => {
    const analysis = detectBottlenecks({
      ram: { capacity: 16, channels: 1 },
    });
    
    expect(analysis.primary?.reason).toContain('Single channel');
    expect(analysis.primary?.impact).toBeGreaterThan(10);
  });

  it('should prioritize severe bottlenecks', () => {
    const analysis = detectBottlenecks({
      cpu: { model: 'Intel i3-10100' }, // Will be severe with GPU
      gpu: { model: 'RTX 4090', tier: 'S' },
      ram: { capacity: 8 }, // Will be moderate
      storage: [{ type: 'hdd', capacity: 500 }], // Will be severe
    });
    
    // Should list storage or CPU as primary (both severe)
    expect(['cpu', 'storage']).toContain(analysis.primary?.component);
    expect(analysis.primary?.severity).toBe('severe');
  });
});

describe('Integration Tests', () => {
  it('should work together for complete analysis', () => {
    const components = {
      cpu: 'AMD Ryzen 7 5800X',
      gpu: 'RTX 3070',
      ram: { capacity: 16, speed: 3200, channels: 2 },
      storage: [{ type: 'nvme', capacity: 1024 }],
    };
    
    const benchmark = predictBenchmarkScore(components);
    const tier = getPerformanceTier(benchmark.overall);
    const bottlenecks = detectBottlenecks({
      cpu: { model: components.cpu },
      gpu: { model: components.gpu },
      ram: components.ram,
      storage: components.storage,
    });
    
    expect(tier.tier).toBe('High-End');
    expect(bottlenecks.balanced).toBe(true);
    expect(benchmark.confidence).toBe('high');
  });

  it('should identify gaming vs productivity builds', () => {
    // Gaming build (GPU-heavy)
    const gamingBuild = predictBenchmarkScore({
      cpu: 'Intel i5-12400',
      gpu: 'RTX 3080',
      ram: { capacity: 16 },
      storage: [{ type: 'ssd', capacity: 512 }],
    });
    
    // Productivity build (CPU-heavy)
    const productivityBuild = predictBenchmarkScore({
      cpu: 'AMD Ryzen 9 5950X',
      gpu: 'RTX 3060',
      ram: { capacity: 64 },
      storage: [{ type: 'nvme', capacity: 2048 }],
    });
    
    expect(gamingBuild.gaming).toBeGreaterThan(gamingBuild.productivity);
    expect(productivityBuild.productivity).toBeGreaterThan(productivityBuild.gaming);
  });
});