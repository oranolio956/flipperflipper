// Data Exporter v3.9.0 - Multi-format Export System
class DataExporter {
  constructor() {
    this.exportFormats = {
      csv: this.exportCSV.bind(this),
      json: this.exportJSON.bind(this)
    };
  }
  
  async export(dataType, format = 'csv') {
    try {
      console.log(`[Exporter] Exporting ${dataType} as ${format}`);
      
      const data = await this.getData(dataType);
      if (!data || data.length === 0) {
        throw new Error(`No ${dataType} data available to export`);
      }
      
      const exportHandler = this.exportFormats[format];
      if (!exportHandler) {
        throw new Error(`Unsupported format: ${format}`);
      }
      
      return await exportHandler(data, dataType);
    } catch (error) {
      console.error('[Exporter] Export failed:', error);
      throw error;
    }
  }
  
  async getData(dataType) {
    const dataMap = {
      listings: 'listings',
      deals: 'deals',
      settings: 'settings'
    };
    
    const storageKey = dataMap[dataType];
    if (!storageKey) {
      throw new Error(`Unknown data type: ${dataType}`);
    }
    
    const result = await chrome.storage.local.get(storageKey);
    let data = result[storageKey] || [];
    
    return Array.isArray(data) ? data : [data];
  }
  
  async exportCSV(data, dataType) {
    const headers = this.getHeaders(data[0], dataType);
    const rows = [];
    
    // Add headers
    rows.push(headers.map(h => this.escapeCSV(h.label)).join(','));
    
    // Convert data to rows
    for (const item of data) {
      const row = headers.map(header => {
        const value = this.getNestedValue(item, header.key);
        return this.escapeCSV(this.formatValue(value, header.type));
      });
      rows.push(row.join(','));
    }
    
    // Create CSV content
    const csvContent = rows.join('\n');
    const blob = new Blob(['\ufeff' + csvContent], { 
      type: 'text/csv;charset=utf-8;' 
    });
    
    // Download file
    const filename = `${dataType}_export_${this.getTimestamp()}.csv`;
    this.downloadFile(blob, filename);
    
    return {
      format: 'csv',
      filename: filename,
      rows: data.length
    };
  }
  
  async exportJSON(data, dataType) {
    const exportData = {
      metadata: {
        type: dataType,
        exportDate: new Date().toISOString(),
        version: chrome.runtime.getManifest().version,
        count: data.length
      },
      data: data
    };
    
    const jsonString = JSON.stringify(exportData, null, 2);
    const blob = new Blob([jsonString], { 
      type: 'application/json' 
    });
    
    const filename = `${dataType}_export_${this.getTimestamp()}.json`;
    this.downloadFile(blob, filename);
    
    return {
      format: 'json',
      filename: filename,
      records: data.length
    };
  }
  
  getHeaders(sample, dataType) {
    const headerConfigs = {
      listings: [
        { key: 'id', label: 'ID', type: 'string' },
        { key: 'title', label: 'Title', type: 'string' },
        { key: 'price', label: 'Price', type: 'currency' },
        { key: 'platform', label: 'Platform', type: 'string' },
        { key: 'location', label: 'Location', type: 'string' },
        { key: 'url', label: 'URL', type: 'url' },
        { key: 'scannedAt', label: 'Scanned At', type: 'datetime' }
      ],
      deals: [
        { key: 'id', label: 'Deal ID', type: 'string' },
        { key: 'listing.title', label: 'Title', type: 'string' },
        { key: 'stage', label: 'Stage', type: 'string' },
        { key: 'listing.price', label: 'Ask Price', type: 'currency' },
        { key: 'createdAt', label: 'Created', type: 'datetime' }
      ]
    };
    
    return headerConfigs[dataType] || [];
  }
  
  getNestedValue(obj, path) {
    return path.split('.').reduce((current, key) => current?.[key], obj);
  }
  
  formatValue(value, type) {
    if (value === null || value === undefined) return '';
    
    switch (type) {
      case 'currency':
        return typeof value === 'number' ? `$${value.toFixed(2)}` : value;
      case 'datetime':
        return value instanceof Date ? value.toLocaleString() : 
               typeof value === 'string' ? new Date(value).toLocaleString() : value;
      default:
        return String(value);
    }
  }
  
  escapeCSV(value) {
    if (typeof value !== 'string') value = String(value);
    
    if (value.includes('"') || value.includes(',') || value.includes('\n')) {
      return `"${value.replace(/"/g, '""')}"`;
    }
    
    return value;
  }
  
  getTimestamp() {
    const now = new Date();
    return now.toISOString().replace(/[:.]/g, '-').slice(0, -5);
  }
  
  downloadFile(blob, filename) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }
}

// Create singleton instance
window.dataExporter = new DataExporter();
