/**
 * Tests for Gallery Navigator
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { scanGallery, createGalleryScannerUI, type GalleryPhoto } from '../galleryNavigator';

// Mock DOM
beforeEach(() => {
  document.body.innerHTML = '';
});

describe('Gallery Navigator', () => {
  it('should find gallery container', async () => {
    // Mock gallery with images
    document.body.innerHTML = `
      <div role="dialog">
        <img src="photo1.jpg" alt="Photo 1">
        <img src="photo2.jpg" alt="Photo 2">
        <button aria-label="Next">Next</button>
      </div>
    `;
    
    const photos = await scanGallery();
    
    expect(photos).toHaveLength(2);
    expect(photos[0].url).toContain('photo1.jpg');
  });

  it('should extract photo metadata', async () => {
    document.body.innerHTML = `
      <div class="gallery">
        <img src="https://example.com/photo1.jpg" alt="Gaming PC Front View">
      </div>
    `;
    
    const photos = await scanGallery();
    
    expect(photos[0]).toMatchObject({
      url: 'https://example.com/photo1.jpg',
      index: 0,
      caption: 'Gaming PC Front View',
    });
  });

  it('should handle Facebook high-res URLs', async () => {
    document.body.innerHTML = `
      <div role="dialog">
        <img src="https://scontent.fbcdn.net/v/t1.0-9/s720x720/photo.jpg">
      </div>
    `;
    
    const photos = await scanGallery();
    
    // Should remove size restrictions
    expect(photos[0].url).toBe('https://scontent.fbcdn.net/v/t1.0-9/photo.jpg');
  });

  it('should create scanner UI', () => {
    const onScan = vi.fn();
    const ui = createGalleryScannerUI(onScan);
    
    document.body.appendChild(ui);
    
    expect(ui.querySelector('.scanner-header')).toBeTruthy();
    expect(ui.querySelector('.scan-btn')).toBeTruthy();
    
    // Click scan button
    const scanBtn = ui.querySelector('.scan-btn') as HTMLElement;
    scanBtn.click();
    
    expect(onScan).toHaveBeenCalled();
  });

  it('should update progress during scan', async () => {
    const progressUpdates: any[] = [];
    
    document.body.innerHTML = `
      <div class="gallery">
        <img src="photo1.jpg">
        <img src="photo2.jpg">
        <img src="photo3.jpg">
      </div>
    `;
    
    await scanGallery((progress) => {
      progressUpdates.push({
        current: progress.current,
        total: progress.total,
      });
    });
    
    expect(progressUpdates).toHaveLength(3);
    expect(progressUpdates[0]).toEqual({ current: 1, total: 3 });
    expect(progressUpdates[2]).toEqual({ current: 3, total: 3 });
  });
});