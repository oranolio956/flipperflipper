/**
 * Barcode Scanner Module
 * Enables barcode/QR code scanning for inventory management
 */

import { InventoryItem } from '../types';

export interface BarcodeData {
  format: 'qr_code' | 'ean_13' | 'ean_8' | 'code_128' | 'code_39' | 'upc_a' | 'upc_e';
  rawValue: string;
  decodedData?: ProductData;
  confidence: number;
  timestamp: Date;
}

export interface ProductData {
  gtin?: string; // Global Trade Item Number
  manufacturer?: string;
  model?: string;
  name?: string;
  category?: string;
  msrp?: number;
  specs?: Record<string, any>;
  imageUrl?: string;
}

export interface ScanSession {
  id: string;
  startTime: Date;
  endTime?: Date;
  itemsScanned: number;
  location?: string;
  notes?: string;
}

export class BarcodeScanner {
  private stream: MediaStream | null = null;
  private videoElement: HTMLVideoElement | null = null;
  private canvasElement: HTMLCanvasElement | null = null;
  private scanInterval: number | null = null;
  private isScanning = false;
  private currentSession: ScanSession | null = null;
  
  // Product database cache
  private productCache: Map<string, ProductData> = new Map();
  
  constructor() {
    this.loadProductCache();
  }

  /**
   * Initialize camera for scanning
   */
  async initializeCamera(videoElement: HTMLVideoElement): Promise<void> {
    try {
      this.stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: 'environment', // Use back camera on mobile
          width: { ideal: 1280 },
          height: { ideal: 720 }
        }
      });
      
      this.videoElement = videoElement;
      this.videoElement.srcObject = this.stream;
      await this.videoElement.play();
      
      // Create canvas for image processing
      this.canvasElement = document.createElement('canvas');
      this.canvasElement.width = this.videoElement.videoWidth;
      this.canvasElement.height = this.videoElement.videoHeight;
    } catch (error) {
      throw new Error('Camera access denied or not available');
    }
  }

  /**
   * Start scanning session
   */
  startScanning(location?: string): ScanSession {
    if (this.isScanning) {
      throw new Error('Scanning already in progress');
    }
    
    this.currentSession = {
      id: `scan_${Date.now()}`,
      startTime: new Date(),
      itemsScanned: 0,
      location
    };
    
    this.isScanning = true;
    
    // Start continuous scanning
    this.scanInterval = window.setInterval(() => {
      this.captureAndDecode();
    }, 500); // Scan every 500ms
    
    return this.currentSession;
  }

  /**
   * Stop scanning session
   */
  async stopScanning(): Promise<ScanSession> {
    if (!this.isScanning || !this.currentSession) {
      throw new Error('No scanning session active');
    }
    
    this.isScanning = false;
    
    if (this.scanInterval) {
      clearInterval(this.scanInterval);
      this.scanInterval = null;
    }
    
    if (this.stream) {
      this.stream.getTracks().forEach(track => track.stop());
      this.stream = null;
    }
    
    this.currentSession.endTime = new Date();
    const session = this.currentSession;
    this.currentSession = null;
    
    // Save session
    await this.saveSession(session);
    
    return session;
  }

  /**
   * Capture frame and decode barcode
   */
  private async captureAndDecode(): Promise<void> {
    if (!this.videoElement || !this.canvasElement || !this.isScanning) return;
    
    const context = this.canvasElement.getContext('2d');
    if (!context) return;
    
    // Draw current frame to canvas
    context.drawImage(
      this.videoElement,
      0, 0,
      this.canvasElement.width,
      this.canvasElement.height
    );
    
    // Get image data
    const imageData = context.getImageData(
      0, 0,
      this.canvasElement.width,
      this.canvasElement.height
    );
    
    // Decode barcode
    const result = await this.decodeBarcode(imageData);
    
    if (result) {
      this.onBarcodeDetected(result);
    }
  }

  /**
   * Decode barcode from image data
   */
  private async decodeBarcode(imageData: ImageData): Promise<BarcodeData | null> {
    // In a real implementation, this would use a library like ZXing or QuaggaJS
    // For now, we'll simulate barcode detection
    
    // Simulate random barcode detection (10% chance)
    if (Math.random() > 0.9) {
      const formats: BarcodeData['format'][] = ['qr_code', 'ean_13', 'code_128', 'upc_a'];
      const format = formats[Math.floor(Math.random() * formats.length)];
      
      // Generate mock barcode
      const mockBarcodes = [
        '0885370928914', // EVGA RTX 3070
        '0812674024246', // Corsair RAM
        '0649528787309', // Samsung SSD
        '0735858419437', // Intel CPU
      ];
      
      const rawValue = mockBarcodes[Math.floor(Math.random() * mockBarcodes.length)];
      
      return {
        format,
        rawValue,
        confidence: 0.85 + Math.random() * 0.15,
        timestamp: new Date()
      };
    }
    
    return null;
  }

  /**
   * Handle detected barcode
   */
  private async onBarcodeDetected(barcode: BarcodeData): Promise<void> {
    // Debounce duplicate scans
    const lastScan = await this.getLastScan();
    if (lastScan && 
        lastScan.rawValue === barcode.rawValue && 
        Date.now() - lastScan.timestamp.getTime() < 2000) {
      return;
    }
    
    // Lookup product data
    barcode.decodedData = await this.lookupProduct(barcode.rawValue);
    
    // Store scan
    await this.storeScan(barcode);
    
    // Update session
    if (this.currentSession) {
      this.currentSession.itemsScanned++;
    }
    
    // Emit event
    this.emitScanEvent(barcode);
  }

  /**
   * Lookup product information
   */
  async lookupProduct(barcode: string): Promise<ProductData | undefined> {
    // Check cache first
    if (this.productCache.has(barcode)) {
      return this.productCache.get(barcode);
    }
    
    // In real implementation, would query UPC database API
    // For now, return mock data based on barcode
    const mockProducts: Record<string, ProductData> = {
      '0885370928914': {
        gtin: '0885370928914',
        manufacturer: 'EVGA',
        model: 'RTX 3070 FTW3 Ultra',
        name: 'EVGA GeForce RTX 3070 FTW3 Ultra Gaming',
        category: 'Graphics Card',
        msrp: 679.99,
        specs: {
          memory: '8GB GDDR6',
          coreClock: '1815 MHz',
          interface: 'PCIe 4.0',
          outputs: '3x DisplayPort, 1x HDMI'
        }
      },
      '0812674024246': {
        gtin: '0812674024246',
        manufacturer: 'Corsair',
        model: 'CMK16GX4M2B3200C16',
        name: 'Corsair Vengeance LPX 16GB DDR4-3200',
        category: 'Memory',
        msrp: 79.99,
        specs: {
          capacity: '16GB (2x8GB)',
          speed: 'DDR4-3200',
          latency: 'CL16',
          voltage: '1.35V'
        }
      },
      '0649528787309': {
        gtin: '0649528787309',
        manufacturer: 'Samsung',
        model: '970 EVO Plus 1TB',
        name: 'Samsung 970 EVO Plus NVMe M.2 SSD',
        category: 'Storage',
        msrp: 149.99,
        specs: {
          capacity: '1TB',
          interface: 'NVMe M.2',
          readSpeed: '3500 MB/s',
          writeSpeed: '3300 MB/s'
        }
      },
      '0735858419437': {
        gtin: '0735858419437',
        manufacturer: 'Intel',
        model: 'i7-10700K',
        name: 'Intel Core i7-10700K Processor',
        category: 'CPU',
        msrp: 374.99,
        specs: {
          cores: '8',
          threads: '16',
          baseClock: '3.8 GHz',
          boostClock: '5.1 GHz',
          tdp: '125W'
        }
      }
    };
    
    const product = mockProducts[barcode];
    
    if (product) {
      // Cache for future use
      this.productCache.set(barcode, product);
      await this.saveProductCache();
    }
    
    return product;
  }

  /**
   * Create inventory item from barcode
   */
  async createInventoryItem(
    barcode: BarcodeData,
    additionalData?: Partial<InventoryItem>
  ): Promise<InventoryItem> {
    const product = barcode.decodedData;
    
    const item: InventoryItem = {
      id: `inv_${Date.now()}`,
      barcode: barcode.rawValue,
      name: product?.name || 'Unknown Product',
      category: product?.category || 'Other',
      quantity: 1,
      purchasePrice: 0,
      currentValue: product?.msrp || 0,
      condition: 'new',
      location: this.currentSession?.location || 'Main Inventory',
      dateAdded: new Date(),
      lastUpdated: new Date(),
      specifications: product?.specs || {},
      notes: '',
      images: [],
      ...additionalData
    };
    
    // Store inventory item
    await this.storeInventoryItem(item);
    
    return item;
  }

  /**
   * Bulk scan mode for multiple items
   */
  async bulkScan(
    items: Array<{ barcode: string; quantity: number; condition: string }>
  ): Promise<InventoryItem[]> {
    const inventoryItems: InventoryItem[] = [];
    
    for (const item of items) {
      const barcodeData: BarcodeData = {
        format: 'ean_13',
        rawValue: item.barcode,
        confidence: 1,
        timestamp: new Date()
      };
      
      barcodeData.decodedData = await this.lookupProduct(item.barcode);
      
      const inventoryItem = await this.createInventoryItem(barcodeData, {
        quantity: item.quantity,
        condition: item.condition as any
      });
      
      inventoryItems.push(inventoryItem);
    }
    
    return inventoryItems;
  }

  /**
   * Generate inventory report
   */
  async generateInventoryReport(): Promise<{
    totalItems: number;
    totalValue: number;
    categories: Record<string, { count: number; value: number }>;
    topValueItems: InventoryItem[];
    lowStockItems: InventoryItem[];
  }> {
    const inventory = await this.getAllInventoryItems();
    
    const report = {
      totalItems: 0,
      totalValue: 0,
      categories: {} as Record<string, { count: number; value: number }>,
      topValueItems: [] as InventoryItem[],
      lowStockItems: [] as InventoryItem[]
    };
    
    // Calculate totals and categorize
    inventory.forEach(item => {
      report.totalItems += item.quantity;
      report.totalValue += item.currentValue * item.quantity;
      
      if (!report.categories[item.category]) {
        report.categories[item.category] = { count: 0, value: 0 };
      }
      
      report.categories[item.category].count += item.quantity;
      report.categories[item.category].value += item.currentValue * item.quantity;
      
      // Track low stock (less than 2)
      if (item.quantity < 2) {
        report.lowStockItems.push(item);
      }
    });
    
    // Get top value items
    report.topValueItems = inventory
      .sort((a, b) => b.currentValue - a.currentValue)
      .slice(0, 10);
    
    return report;
  }

  /**
   * Export inventory to CSV
   */
  exportInventoryCSV(): string {
    const inventory = this.getAllInventoryItemsSync();
    
    const headers = [
      'Barcode',
      'Name',
      'Category',
      'Quantity',
      'Purchase Price',
      'Current Value',
      'Total Value',
      'Condition',
      'Location',
      'Date Added',
      'Notes'
    ];
    
    const rows = inventory.map(item => [
      item.barcode || '',
      item.name,
      item.category,
      item.quantity.toString(),
      item.purchasePrice.toFixed(2),
      item.currentValue.toFixed(2),
      (item.currentValue * item.quantity).toFixed(2),
      item.condition,
      item.location,
      new Date(item.dateAdded).toLocaleDateString(),
      item.notes || ''
    ]);
    
    const csv = [
      headers.join(','),
      ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
    ].join('\n');
    
    return csv;
  }

  /**
   * Emit scan event
   */
  private emitScanEvent(barcode: BarcodeData): void {
    const event = new CustomEvent('barcode-scanned', {
      detail: barcode
    });
    window.dispatchEvent(event);
  }

  /**
   * Data persistence methods
   */
  private async storeScan(barcode: BarcodeData): Promise<void> {
    const { barcodeScans = [] } = await chrome.storage.local.get('barcodeScans');
    barcodeScans.push(barcode);
    
    // Keep only last 1000 scans
    if (barcodeScans.length > 1000) {
      barcodeScans.splice(0, barcodeScans.length - 1000);
    }
    
    await chrome.storage.local.set({ barcodeScans });
  }

  private async getLastScan(): Promise<BarcodeData | null> {
    const { barcodeScans = [] } = await chrome.storage.local.get('barcodeScans');
    return barcodeScans.length > 0 ? barcodeScans[barcodeScans.length - 1] : null;
  }

  private async storeInventoryItem(item: InventoryItem): Promise<void> {
    const { inventory = {} } = await chrome.storage.local.get('inventory');
    inventory[item.id] = item;
    await chrome.storage.local.set({ inventory });
  }

  private async getAllInventoryItems(): Promise<InventoryItem[]> {
    const { inventory = {} } = await chrome.storage.local.get('inventory');
    return Object.values(inventory);
  }

  private getAllInventoryItemsSync(): InventoryItem[] {
    // In real implementation, would use sync storage
    return [];
  }

  private async saveSession(session: ScanSession): Promise<void> {
    const { scanSessions = [] } = await chrome.storage.local.get('scanSessions');
    scanSessions.push(session);
    await chrome.storage.local.set({ scanSessions });
  }

  private async loadProductCache(): Promise<void> {
    const { productCache = {} } = await chrome.storage.local.get('productCache');
    this.productCache = new Map(Object.entries(productCache));
  }

  private async saveProductCache(): Promise<void> {
    const productCache = Object.fromEntries(this.productCache);
    await chrome.storage.local.set({ productCache });
  }

  /**
   * Check if scanning is active
   */
  get isActive(): boolean {
    return this.isScanning;
  }

  /**
   * Get current session
   */
  get session(): ScanSession | null {
    return this.currentSession;
  }
}

// Export singleton instance
export const barcodeScanner = new BarcodeScanner();