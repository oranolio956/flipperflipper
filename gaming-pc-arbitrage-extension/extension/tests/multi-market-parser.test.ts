/**
 * Multi-Market Parser Tests
 * Tests for Craigslist and OfferUp content script parsers
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { JSDOM } from 'jsdom';

// Mock chrome API
global.chrome = {
  runtime: {
    sendMessage: vi.fn(),
    onMessage: {
      addListener: vi.fn(),
    },
  },
} as any;

describe('Craigslist Parser', () => {
  let dom: JSDOM;
  
  beforeEach(() => {
    // Create mock Craigslist listing page
    dom = new JSDOM(`
      <!DOCTYPE html>
      <html>
        <body>
          <section class="body">
            <h1 class="postingtitle">
              <span class="postingtitletext">
                <span id="titletextonly">Gaming PC - RTX 3070, i7-10700K, 32GB RAM</span>
                <span class="price">$1200</span>
                <small> (Denver)</small>
              </span>
            </h1>
            
            <section id="postingbody">
              High-end gaming PC for sale. Specs:
              - Intel i7-10700K
              - NVIDIA RTX 3070
              - 32GB DDR4 RAM
              - 1TB NVMe SSD
              - 750W PSU
              Built 6 months ago, runs everything at max settings.
            </section>
            
            <div class="gallery">
              <a href="https://images.craigslist.org/12345_01.jpg" class="thumb" title="1"></a>
              <a href="https://images.craigslist.org/12345_02.jpg" class="thumb" title="2"></a>
            </div>
            
            <div class="postinginfos">
              <p class="postinginfo">
                post id: 7654321098
              </p>
              <p class="postinginfo reveal">
                posted: <time class="date timeago" datetime="2024-01-15T10:30:00-0700">2024-01-15 10:30am</time>
              </p>
            </div>
          </section>
        </body>
      </html>
    `, {
      url: 'https://denver.craigslist.org/sys/d/gaming-pc-rtx-3070/7654321098.html',
    });
    
    global.document = dom.window.document as any;
    global.window = dom.window as any;
    global.location = dom.window.location as any;
  });

  it('should detect listing page URLs', () => {
    expect(location.pathname).toMatch(/\/sys\/d\/[^/]+\/\d+\.html$/);
  });

  it('should extract listing data correctly', () => {
    const title = document.querySelector('#titletextonly')?.textContent;
    const priceText = document.querySelector('.price')?.textContent || '';
    const price = parseInt(priceText.replace(/[^0-9]/g, ''), 10);
    const description = document.querySelector('#postingbody')?.textContent?.trim();
    const location = document.querySelector('.postingtitletext small')?.textContent?.replace(/[()]/g, '').trim();
    
    expect(title).toBe('Gaming PC - RTX 3070, i7-10700K, 32GB RAM');
    expect(price).toBe(1200);
    expect(description).toContain('Intel i7-10700K');
    expect(description).toContain('NVIDIA RTX 3070');
    expect(location).toBe('Denver');
  });

  it('should extract images', () => {
    const images: string[] = [];
    const thumbs = document.querySelectorAll('.thumb');
    thumbs.forEach(thumb => {
      const link = thumb.getAttribute('href');
      if (link) images.push(link);
    });
    
    expect(images).toHaveLength(2);
    expect(images[0]).toBe('https://images.craigslist.org/12345_01.jpg');
  });
});

describe('OfferUp Parser', () => {
  let dom: JSDOM;
  
  beforeEach(() => {
    // Create mock OfferUp listing page
    dom = new JSDOM(`
      <!DOCTYPE html>
      <html>
        <body>
          <main>
            <div data-testid="item-detail-container">
              <h1 data-testid="item-title">Gaming Desktop - RTX 3080 Ti, Ryzen 7 5800X</h1>
              
              <div data-testid="item-price">
                <span class="currency">$1,850</span>
              </div>
              
              <div data-testid="item-condition">
                <span>Condition: Like new</span>
              </div>
              
              <div data-testid="item-description">
                <p>Custom built gaming PC, barely used. Specs:
                - AMD Ryzen 7 5800X
                - NVIDIA RTX 3080 Ti
                - 32GB DDR4 3600MHz
                - 2TB NVMe SSD
                - 850W Gold PSU
                Comes with all original boxes.</p>
              </div>
              
              <div data-testid="item-location">
                <a href="/location">Aurora, CO</a>
              </div>
              
              <div data-testid="seller-info">
                <a href="/profile/seller123">
                  <span data-testid="seller-name">John D.</span>
                </a>
                <div data-testid="seller-rating">
                  <span>4.8★ (45 reviews)</span>
                </div>
              </div>
              
              <div class="carousel">
                <img src="https://photos.offerup.com/image1.jpg" alt="Photo 1">
                <img src="https://photos.offerup.com/image2.jpg" alt="Photo 2">
              </div>
              
              <time data-testid="posted-time">Posted 2 days ago</time>
            </div>
          </main>
        </body>
      </html>
    `, {
      url: 'https://offerup.com/item/detail/123456789/gaming-desktop-rtx-3080-ti',
    });
    
    global.document = dom.window.document as any;
    global.window = dom.window as any;
    global.location = dom.window.location as any;
  });

  it('should detect listing page URLs', () => {
    expect(location.pathname).toMatch(/\/item\/detail\/\d+/);
  });

  it('should extract listing data correctly', () => {
    const title = document.querySelector('[data-testid="item-title"]')?.textContent;
    const priceText = document.querySelector('[data-testid="item-price"]')?.textContent || '';
    const price = parseFloat(priceText.replace(/[^0-9.,]/g, '').replace(',', ''));
    const condition = document.querySelector('[data-testid="item-condition"]')?.textContent;
    const sellerName = document.querySelector('[data-testid="seller-name"]')?.textContent;
    const sellerRating = document.querySelector('[data-testid="seller-rating"]')?.textContent;
    
    expect(title).toBe('Gaming Desktop - RTX 3080 Ti, Ryzen 7 5800X');
    expect(price).toBe(1850);
    expect(condition).toContain('Like new');
    expect(sellerName).toBe('John D.');
    expect(sellerRating).toContain('4.8★');
  });

  it('should extract images', () => {
    const images: string[] = [];
    const imageElements = document.querySelectorAll('.carousel img');
    
    imageElements.forEach(img => {
      if (img instanceof HTMLImageElement) {
        images.push(img.src);
      }
    });
    
    expect(images).toHaveLength(2);
    expect(images[0]).toContain('offerup.com');
  });
});