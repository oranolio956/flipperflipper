/**
 * Inventory Manager
 * Track owned items, parts, and stock levels
 */

export interface InventoryItem {
  id: string;
  type: 'complete-system' | 'component' | 'accessory';
  status: 'available' | 'reserved' | 'testing' | 'listed' | 'sold';
  
  // Item details
  name: string;
  category?: string;
  specs?: Record<string, any>;
  serial?: string;
  
  // Acquisition
  acquiredDate: Date;
  acquiredFrom: {
    dealId?: string;
    source: string;
    price: number;
  };
  
  // Condition
  condition: 'new' | 'like-new' | 'good' | 'fair' | 'for-parts';
  testedDate?: Date;
  issues?: string[];
  
  // Location
  location: {
    type: 'home' | 'storage' | 'in-transit' | 'with-buyer';
    details?: string;
    bin?: string;
  };
  
  // Financials
  costs: {
    purchase: number;
    repairs?: number;
    fees?: number;
    total: number;
  };
  
  // Listing info
  listedOn?: {
    platform: string;
    listingId: string;
    price: number;
    date: Date;
  }[];
  
  // Sale info
  soldTo?: {
    buyerId: string;
    price: number;
    date: Date;
    platform: string;
  };
  
  // Metadata
  photos?: string[];
  notes?: string;
  tags?: string[];
}

export interface StockLevel {
  category: string;
  target: number;
  current: number;
  reserved: number;
  available: number;
  reorderPoint: number;
  status: 'good' | 'low' | 'out' | 'excess';
}

export interface InventoryMetrics {
  totalItems: number;
  totalValue: number;
  byStatus: Record<string, number>;
  byCategory: Record<string, number>;
  turnoverRate: number;
  avgHoldingDays: number;
  deadStock: InventoryItem[];
}

/**
 * Add item to inventory
 */
export function addInventoryItem(
  item: Omit<InventoryItem, 'id' | 'costs'>
): InventoryItem {
  const costs = calculateItemCosts(item);
  
  return {
    ...item,
    id: generateInventoryId(),
    costs,
  };
}

/**
 * Update item status
 */
export function updateItemStatus(
  item: InventoryItem,
  newStatus: InventoryItem['status'],
  metadata?: {
    platform?: string;
    listingId?: string;
    price?: number;
    buyerId?: string;
  }
): InventoryItem {
  const updated = { ...item, status: newStatus };
  
  // Handle status-specific updates
  switch (newStatus) {
    case 'listed':
      if (metadata?.platform && metadata?.listingId && metadata?.price) {
        updated.listedOn = [
          ...(updated.listedOn || []),
          {
            platform: metadata.platform,
            listingId: metadata.listingId,
            price: metadata.price,
            date: new Date(),
          },
        ];
      }
      break;
      
    case 'sold':
      if (metadata?.buyerId && metadata?.price) {
        updated.soldTo = {
          buyerId: metadata.buyerId,
          price: metadata.price,
          date: new Date(),
          platform: metadata.platform || 'unknown',
        };
      }
      break;
  }
  
  return updated;
}

/**
 * Calculate stock levels
 */
export function calculateStockLevels(
  items: InventoryItem[],
  targets: Record<string, { target: number; reorderPoint: number }>
): StockLevel[] {
  const levels: StockLevel[] = [];
  const categories = new Set(items.map(i => i.category || 'uncategorized'));
  
  for (const category of categories) {
    const categoryItems = items.filter(i => (i.category || 'uncategorized') === category);
    const current = categoryItems.length;
    const reserved = categoryItems.filter(i => i.status === 'reserved').length;
    const available = categoryItems.filter(i => i.status === 'available').length;
    
    const target = targets[category]?.target || 0;
    const reorderPoint = targets[category]?.reorderPoint || Math.floor(target * 0.3);
    
    let status: StockLevel['status'] = 'good';
    if (available === 0) status = 'out';
    else if (available <= reorderPoint) status = 'low';
    else if (current > target * 1.5) status = 'excess';
    
    levels.push({
      category,
      target,
      current,
      reserved,
      available,
      reorderPoint,
      status,
    });
  }
  
  return levels;
}

/**
 * Get inventory metrics
 */
export function getInventoryMetrics(items: InventoryItem[]): InventoryMetrics {
  const now = new Date();
  
  // Calculate total value
  const totalValue = items.reduce((sum, item) => {
    if (item.status === 'sold' && item.soldTo) {
      return sum + item.soldTo.price;
    } else if (item.listedOn && item.listedOn.length > 0) {
      return sum + item.listedOn[item.listedOn.length - 1].price;
    }
    return sum + item.costs.total;
  }, 0);
  
  // Group by status
  const byStatus = items.reduce((acc, item) => {
    acc[item.status] = (acc[item.status] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);
  
  // Group by category
  const byCategory = items.reduce((acc, item) => {
    const category = item.category || 'uncategorized';
    acc[category] = (acc[category] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);
  
  // Calculate turnover
  const soldItems = items.filter(i => i.status === 'sold' && i.soldTo);
  const avgHoldingDays = soldItems.length > 0
    ? soldItems.reduce((sum, item) => {
        const days = Math.floor(
          (item.soldTo!.date.getTime() - item.acquiredDate.getTime()) / (1000 * 60 * 60 * 24)
        );
        return sum + days;
      }, 0) / soldItems.length
    : 0;
  
  const turnoverRate = avgHoldingDays > 0 ? 365 / avgHoldingDays : 0;
  
  // Find dead stock (items held > 90 days)
  const deadStock = items.filter(item => {
    if (item.status === 'sold') return false;
    const daysHeld = Math.floor(
      (now.getTime() - item.acquiredDate.getTime()) / (1000 * 60 * 60 * 24)
    );
    return daysHeld > 90;
  });
  
  return {
    totalItems: items.length,
    totalValue,
    byStatus,
    byCategory,
    turnoverRate,
    avgHoldingDays,
    deadStock,
  };
}

/**
 * Find items by criteria
 */
export function findInventoryItems(
  items: InventoryItem[],
  criteria: {
    status?: InventoryItem['status'];
    category?: string;
    minValue?: number;
    maxValue?: number;
    location?: string;
    tags?: string[];
    search?: string;
  }
): InventoryItem[] {
  return items.filter(item => {
    if (criteria.status && item.status !== criteria.status) return false;
    if (criteria.category && item.category !== criteria.category) return false;
    if (criteria.minValue && item.costs.total < criteria.minValue) return false;
    if (criteria.maxValue && item.costs.total > criteria.maxValue) return false;
    if (criteria.location && item.location.type !== criteria.location) return false;
    if (criteria.tags && criteria.tags.length > 0) {
      if (!item.tags || !criteria.tags.some(tag => item.tags!.includes(tag))) {
        return false;
      }
    }
    if (criteria.search) {
      const searchLower = criteria.search.toLowerCase();
      const searchableText = [
        item.name,
        item.category,
        item.notes,
        JSON.stringify(item.specs),
      ].join(' ').toLowerCase();
      if (!searchableText.includes(searchLower)) return false;
    }
    return true;
  });
}

/**
 * Suggest items to bundle
 */
export function suggestBundles(
  items: InventoryItem[],
  targetValue?: number
): {
  bundle: InventoryItem[];
  totalValue: number;
  compatibility: 'full' | 'partial' | 'none';
  reasoning: string;
}[] {
  const availableItems = items.filter(i => i.status === 'available');
  const suggestions: any[] = [];
  
  // Try to find complete system bundles
  const systems = availableItems.filter(i => i.type === 'complete-system');
  const components = availableItems.filter(i => i.type === 'component');
  
  // Suggest upgrading systems with components
  for (const system of systems) {
    const compatibleComponents = findCompatibleComponents(system, components);
    if (compatibleComponents.length > 0) {
      suggestions.push({
        bundle: [system, ...compatibleComponents],
        totalValue: system.costs.total + compatibleComponents.reduce((sum, c) => sum + c.costs.total, 0),
        compatibility: 'full',
        reasoning: 'System upgrade bundle - adds value to base system',
      });
    }
  }
  
  // Suggest component bundles
  const gpus = components.filter(c => c.category === 'gpu');
  const cpus = components.filter(c => c.category === 'cpu');
  const rams = components.filter(c => c.category === 'ram');
  
  if (gpus.length > 0 && cpus.length > 0) {
    suggestions.push({
      bundle: [gpus[0], cpus[0], ...(rams.length > 0 ? [rams[0]] : [])],
      totalValue: gpus[0].costs.total + cpus[0].costs.total + (rams[0]?.costs.total || 0),
      compatibility: 'partial',
      reasoning: 'Core component bundle - attractive to builders',
    });
  }
  
  // Filter by target value if specified
  if (targetValue) {
    return suggestions.filter(s => 
      s.totalValue >= targetValue * 0.8 && s.totalValue <= targetValue * 1.2
    );
  }
  
  return suggestions.slice(0, 5); // Top 5 suggestions
}

/**
 * Calculate restock recommendations
 */
export function calculateRestockRecommendations(
  items: InventoryItem[],
  salesHistory: Array<{ category: string; soldDate: Date; price: number }>,
  budget: number
): {
  category: string;
  quantity: number;
  estimatedCost: number;
  expectedROI: number;
  reasoning: string;
}[] {
  const recommendations: any[] = [];
  const categories = new Set(salesHistory.map(s => s.category));
  
  for (const category of categories) {
    // Calculate sales velocity
    const categorySales = salesHistory.filter(s => s.category === category);
    const salesPerMonth = categorySales.length / 3; // Assume 3 months history
    
    // Current stock
    const currentStock = items.filter(i => 
      i.category === category && i.status === 'available'
    ).length;
    
    // Calculate ideal stock (1.5 months of sales)
    const idealStock = Math.ceil(salesPerMonth * 1.5);
    const needed = Math.max(0, idealStock - currentStock);
    
    if (needed > 0) {
      const avgSalePrice = categorySales.reduce((sum, s) => sum + s.price, 0) / categorySales.length;
      const avgCost = avgSalePrice * 0.7; // Assume 30% margin
      const estimatedCost = needed * avgCost;
      
      if (estimatedCost <= budget) {
        recommendations.push({
          category,
          quantity: needed,
          estimatedCost,
          expectedROI: 0.3,
          reasoning: `Sales velocity: ${salesPerMonth.toFixed(1)}/month, current stock: ${currentStock}`,
        });
      }
    }
  }
  
  // Sort by ROI
  return recommendations
    .sort((a, b) => b.expectedROI - a.expectedROI)
    .slice(0, 5);
}

// Helper functions
function calculateItemCosts(item: Partial<InventoryItem>): InventoryItem['costs'] {
  const purchase = item.acquiredFrom?.price || 0;
  const repairs = 0; // Would come from repair tracking
  const fees = purchase * 0.13; // Platform fees estimate
  
  return {
    purchase,
    repairs,
    fees,
    total: purchase + repairs + fees,
  };
}

function generateInventoryId(): string {
  return `INV-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

function findCompatibleComponents(
  system: InventoryItem,
  components: InventoryItem[]
): InventoryItem[] {
  // Simplified compatibility check
  const compatible: InventoryItem[] = [];
  
  // Check for RAM upgrades
  const systemRam = system.specs?.ram;
  if (systemRam && parseInt(systemRam) < 32) {
    const ramUpgrades = components.filter(c => 
      c.category === 'ram' && parseInt(c.specs?.capacity || '0') > parseInt(systemRam)
    );
    compatible.push(...ramUpgrades);
  }
  
  // Check for storage upgrades
  if (!system.specs?.storage?.includes('nvme')) {
    const nvmeUpgrades = components.filter(c => 
      c.category === 'storage' && c.specs?.type === 'nvme'
    );
    compatible.push(...nvmeUpgrades);
  }
  
  return compatible.slice(0, 2); // Max 2 upgrades
}