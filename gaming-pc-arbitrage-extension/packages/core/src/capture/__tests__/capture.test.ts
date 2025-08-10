/**
 * Tests for Capture Modules
 */

import { describe, it, expect } from 'vitest';
import {
  extractSpecsFromText,
  preprocessImage,
  calculateConfidence,
} from '../../ocr/photoExtractor';
import {
  parseQuickAddText,
  parsePastedContent,
} from '../quickAdd';
import {
  parseVoiceTranscript,
  generateVoicePrompts,
  formatVoiceNote,
} from '../voiceNotes';

describe('Photo OCR', () => {
  it('should extract specs from OCR text', () => {
    const text = `
      Gaming PC Build
      Intel Core i7-12700K
      NVIDIA RTX 3080 Ti
      32GB DDR4 3200MHz
      1TB NVMe SSD + 2TB HDD
      ASUS Z690 Motherboard
      850W 80+ Gold PSU
    `;
    
    const specs = extractSpecsFromText(text);
    
    expect(specs.cpu).toBe('i7 12700k');
    expect(specs.gpu).toBe('rtx 3080 ti');
    expect(specs.ram).toBe('32gb 3200mhz');
    expect(specs.storage).toContain('1tb nvme');
    expect(specs.motherboard).toContain('z690');
    expect(specs.psu).toBe('850w');
  });

  it('should handle messy OCR text', () => {
    const text = "lntel i5-I2400.. RTX3060.. l6GB RAM";
    
    const specs = extractSpecsFromText(text);
    
    expect(specs.cpu).toContain('i5');
    expect(specs.gpu).toContain('rtx');
    expect(specs.ram).toBeTruthy();
  });

  it('should preprocess image data', () => {
    const imageData = new ImageData(
      new Uint8ClampedArray([255, 0, 0, 255, 0, 255, 0, 255]), // Red and green pixels
      2,
      1
    );
    
    const processed = preprocessImage(imageData);
    
    // Should be grayscale
    expect(processed.data[0]).toBe(processed.data[1]);
    expect(processed.data[0]).toBe(processed.data[2]);
  });

  it('should calculate OCR confidence', () => {
    const regions = [
      { text: 'RTX 3080', bbox: { x: 0, y: 0, width: 100, height: 20 }, confidence: 0.95 },
      { text: 'Intel i7', bbox: { x: 0, y: 30, width: 100, height: 20 }, confidence: 0.90 },
    ];
    
    const specs = { cpu: 'Intel i7', gpu: 'RTX 3080' };
    
    const confidence = calculateConfidence(regions, specs);
    
    expect(confidence).toBeGreaterThan(0.9); // High confidence with key specs found
  });
});

describe('Quick Add', () => {
  it('should parse single line input', () => {
    const input = 'Gaming PC i7-12700K RTX 3070 16GB $850';
    
    const result = parseQuickAddText(input);
    
    expect(result.listing.price).toBe(850);
    expect(result.listing.specs.cpu).toContain('i7');
    expect(result.listing.specs.gpu).toContain('RTX 3070');
    expect(result.listing.specs.ram).toBe('16GB');
    expect(result.validation.isValid).toBe(true);
  });

  it('should parse multi-line input', () => {
    const input = `
      High-End Gaming Build
      Price: $1200
      CPU: AMD Ryzen 7 5800X
      GPU: RTX 3080
      RAM: 32GB DDR4
      Storage: 1TB NVMe
    `;
    
    const result = parseQuickAddText(input);
    
    expect(result.listing.title).toBe('High-End Gaming Build');
    expect(result.listing.price).toBe(1200);
    expect(result.listing.specs.cpu).toContain('Ryzen 7 5800X');
    expect(result.listing.specs.gpu).toBe('RTX 3080');
  });

  it('should validate price range', () => {
    const result = parseQuickAddText('PC $25000'); // Too high
    
    expect(result.validation.isValid).toBe(false);
    expect(result.validation.errors).toContain('Invalid price (must be $50-$10,000)');
  });

  it('should generate title from specs', () => {
    const result = parseQuickAddText('i5-12400 RTX 3060 16GB $700');
    
    expect(result.listing.title).toContain('Gaming PC');
    expect(result.listing.title).toContain('i5');
  });

  it('should provide normalization suggestions', () => {
    const result = parseQuickAddText('intel core i7 12700k');
    
    const cpuSuggestion = result.suggestions.find(s => s.field === 'cpu');
    expect(cpuSuggestion).toBeTruthy();
    expect(cpuSuggestion?.suggested).toBe('Intel Core i7 12700k');
  });

  it('should parse Facebook paste', () => {
    const fbPaste = `
      Gaming PC - Like New
      $800 · In stock
      
      Specs:
      - Intel i5-12600K
      - RTX 3060 Ti
      - 16GB RAM
    `;
    
    const result = parsePastedContent(fbPaste);
    
    expect(result.listing.price).toBe(800);
    expect(result.listing.specs.cpu).toContain('i5-12600K');
    expect(result.listing.source).toBe('paste');
  });
});

describe('Voice Notes', () => {
  it('should parse listing creation from voice', () => {
    const transcript = 'Create new listing price is 950 dollars CPU is i7 12700K GPU is RTX 3070 Ti';
    
    const result = parseVoiceTranscript(transcript);
    
    expect(result.type).toBe('listing');
    expect(result.data.price).toBe(950);
    expect(result.data.cpu).toContain('i7');
    expect(result.data.gpu).toBe('RTX 3070 TI');
    expect(result.commands).toHaveLength(3); // price, cpu, gpu
  });

  it('should handle phonetic variations', () => {
    const transcript = 'CPU is eye seven twelve thousand seven hundred';
    
    const result = parseVoiceTranscript(transcript);
    
    expect(result.data.cpu).toContain('i7');
    expect(result.data.cpu).toContain('12700');
  });

  it('should parse follow-up commands', () => {
    const transcript = 'Follow up in 2 days about this deal';
    
    const result = parseVoiceTranscript(transcript);
    
    expect(result.type).toBe('followup');
    expect(result.data.followUpHours).toBe(48);
    expect(result.commands[0].command).toBe('schedule_followup');
  });

  it('should parse action commands', () => {
    const transcript = 'Mark as sold for asking price';
    
    const result = parseVoiceTranscript(transcript);
    
    expect(result.commands).toHaveLength(1);
    expect(result.commands[0].command).toBe('mark_sold');
    expect(result.commands[0].confidence).toBeGreaterThan(0.9);
  });

  it('should normalize GPU names from voice', () => {
    const transcript = 'GPU is are tx thirty eighty tea eye';
    
    const result = parseVoiceTranscript(transcript);
    
    expect(result.data.gpu).toBe('RTX 3080 TI');
  });

  it('should generate context-aware prompts', () => {
    const prompts = generateVoicePrompts({
      stage: 'listing',
      hasPrice: false,
      hasSpecs: false,
    });
    
    expect(prompts).toContain('Say the price, like "Price is 800 dollars"');
    expect(prompts).toContain('Describe the specs, like "CPU is i7 12700, GPU is RTX 3070"');
  });

  it('should format voice notes', () => {
    const note = {
      id: '123',
      timestamp: new Date(Date.now() - 3600000), // 1 hour ago
      duration: 15,
      transcript: 'New listing for gaming PC with RTX 3080 and i7 processor',
      confidence: 0.9,
      type: 'listing' as const,
    };
    
    const formatted = formatVoiceNote(note);
    
    expect(formatted).toContain('📦 Listing:');
    expect(formatted).toContain('New listing for gaming PC');
  });
});