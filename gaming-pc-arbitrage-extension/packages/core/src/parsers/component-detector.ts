/**
 * Component Detection Engine
 * Uses regex patterns and heuristics to identify PC components from text
 */

import {
  CPUComponent,
  GPUComponent,
  RAMComponent,
  StorageComponent,
  MotherboardComponent,
  PSUComponent,
  CaseComponent,
  CoolingComponent,
  Listing,
} from '../types';

export class ComponentDetector {
  // CPU Detection Patterns
  private cpuPatterns = {
    intel: {
      // Modern Intel patterns: i3/i5/i7/i9-XXXX(K/F/KF)
      modern: /(?:intel\s*)?(?:core\s*)?i[3579][\s-]*(\d{4,5}[A-Z]{0,2})/gi,
      // Xeon patterns
      xeon: /xeon\s*(?:e[35]-)?(\d{4})/gi,
      // Older patterns: i7 920, i5 2500K
      legacy: /(?:intel\s*)?(?:core\s*)?i[357]\s+(\d{3,4}[A-Z]?)/gi,
    },
    amd: {
      // Ryzen patterns: Ryzen 5 5600X, Ryzen 7 3700X
      ryzen: /ryzen\s*([3579])\s*(\d{4}[A-Z]{0,2})/gi,
      // Threadripper
      threadripper: /threadripper\s*(\d{4}[A-Z]?)/gi,
      // Older FX series
      fx: /fx[\s-]*(\d{4})/gi,
    },
  };

  // GPU Detection Patterns
  private gpuPatterns = {
    nvidia: {
      // RTX patterns: RTX 3060, RTX 3060 Ti, RTX 4070
      rtx: /rtx\s*(\d{4})(?:\s*(ti|super))?(?:\s*(\d+)\s*gb)?/gi,
      // GTX patterns: GTX 1060, GTX 1660 Ti
      gtx: /gtx\s*(\d{3,4})(?:\s*(ti|super))?(?:\s*(\d+)\s*gb)?/gi,
      // Quadro patterns
      quadro: /quadro\s*([a-z]?\d{4})/gi,
    },
    amd: {
      // RX patterns: RX 580, RX 6700 XT
      rx: /rx\s*(\d{3,4})(?:\s*(xt))?(?:\s*(\d+)\s*gb)?/gi,
      // Older R9/R7 patterns
      r9r7: /r[79]\s*(\d{3,4})/gi,
      // Radeon VII
      vii: /radeon\s*vii/gi,
    },
    intel: {
      // Arc patterns: Arc A750, Arc A770
      arc: /arc\s*a(\d{3,4})/gi,
    },
  };

  // RAM Detection Patterns
  private ramPatterns = {
    ddr5: /(\d+)\s*gb\s*ddr5(?:\s*(\d{4,5}))?/gi,
    ddr4: /(\d+)\s*gb\s*ddr4(?:\s*(\d{4,5}))?/gi,
    ddr3: /(\d+)\s*gb\s*ddr3(?:\s*(\d{4}))?/gi,
    generic: /(\d+)\s*gb\s*(?:ram|memory)/gi,
  };

  // Storage Detection Patterns
  private storagePatterns = {
    nvme: /(\d+)\s*(?:gb|tb)\s*(?:nvme|m\.2)/gi,
    ssd: /(\d+)\s*(?:gb|tb)\s*ssd/gi,
    hdd: /(\d+)\s*(?:gb|tb)\s*(?:hdd|hard\s*drive)/gi,
  };

  // PSU Detection Patterns
  private psuPatterns = {
    wattage: /(\d{3,4})\s*w(?:att)?/gi,
    efficiency: /(80\+(?:\s*(?:bronze|silver|gold|platinum|titanium))?)/gi,
  };

  /**
   * Detect all components from text
   */
  async detectAllComponents(text: string): Promise<Listing['components']> {
    const components: Listing['components'] = {};
    
    // Detect each component type
    components.cpu = this.detectCPU(text);
    components.gpu = this.detectGPU(text);
    components.ram = this.detectRAM(text);
    components.storage = this.detectStorage(text);
    components.motherboard = this.detectMotherboard(text);
    components.psu = this.detectPSU(text);
    components.case = this.detectCase(text);
    components.cooling = this.detectCooling(text);
    
    return components;
  }

  /**
   * Detect CPU from text
   */
  detectCPU(text: string): CPUComponent | undefined {
    // Try Intel patterns
    for (const [key, pattern] of Object.entries(this.cpuPatterns.intel)) {
      const match = pattern.exec(text);
      if (match) {
        const model = match[0].replace(/\s+/g, ' ').trim();
        return this.parseIntelCPU(model);
      }
    }
    
    // Try AMD patterns
    for (const [key, pattern] of Object.entries(this.cpuPatterns.amd)) {
      const match = pattern.exec(text);
      if (match) {
        const model = match[0].replace(/\s+/g, ' ').trim();
        return this.parseAMDCPU(model);
      }
    }
    
    return undefined;
  }

  /**
   * Parse Intel CPU details
   */
  private parseIntelCPU(model: string): CPUComponent {
    // Extract generation from model number
    let generation = 0;
    const genMatch = model.match(/i[3579][\s-]*(\d)/);
    if (genMatch) {
      generation = parseInt(genMatch[1]);
      // Handle 10th gen and above (5 digits)
      if (model.match(/\d{5}/)) {
        generation = parseInt(model.match(/(\d{2})\d{3}/)![1]);
      }
    }
    
    // Determine core count based on model
    let cores = 4;
    let threads = 8;
    if (model.includes('i3')) {
      cores = 4;
      threads = 8;
    } else if (model.includes('i5')) {
      cores = 6;
      threads = generation >= 10 ? 12 : 6;
    } else if (model.includes('i7')) {
      cores = generation >= 10 ? 8 : 4;
      threads = generation >= 10 ? 16 : 8;
    } else if (model.includes('i9')) {
      cores = generation >= 10 ? 10 : 8;
      threads = generation >= 10 ? 20 : 16;
    }
    
    // Estimate TDP
    const tdp = model.includes('K') ? 125 : 65;
    
    return {
      brand: 'Intel',
      model: model,
      generation,
      cores,
      threads,
      baseClock: 3.0, // Default estimate
      tdp,
      socket: generation >= 12 ? 'LGA1700' : generation >= 10 ? 'LGA1200' : 'LGA1151',
      value: 0, // Will be calculated by pricing engine
      condition: 'good', // Default
    };
  }

  /**
   * Parse AMD CPU details
   */
  private parseAMDCPU(model: string): CPUComponent {
    // Extract series and model number
    const ryzenMatch = model.match(/ryzen\s*([3579])\s*(\d{4})/i);
    if (!ryzenMatch) {
      return {
        brand: 'AMD',
        model: model,
        cores: 4,
        threads: 8,
        baseClock: 3.0,
        tdp: 65,
        socket: 'AM4',
        value: 0,
        condition: 'good',
      };
    }
    
    const series = parseInt(ryzenMatch[1]);
    const modelNum = ryzenMatch[2];
    const generation = parseInt(modelNum[0]) * 1000;
    
    // Determine core count based on series
    let cores = 6;
    let threads = 12;
    if (series === 3) {
      cores = 4;
      threads = 8;
    } else if (series === 5) {
      cores = 6;
      threads = 12;
    } else if (series === 7) {
      cores = 8;
      threads = 16;
    } else if (series === 9) {
      cores = generation >= 5000 ? 16 : 12;
      threads = generation >= 5000 ? 32 : 24;
    }
    
    // Determine socket
    const socket = generation >= 7000 ? 'AM5' : 'AM4';
    
    return {
      brand: 'AMD',
      model: model,
      generation,
      cores,
      threads,
      baseClock: 3.6,
      tdp: model.includes('X') ? 105 : 65,
      socket,
      value: 0,
      condition: 'good',
    };
  }

  /**
   * Detect GPU from text
   */
  detectGPU(text: string): GPUComponent | undefined {
    // Try NVIDIA patterns
    for (const [key, pattern] of Object.entries(this.gpuPatterns.nvidia)) {
      const match = pattern.exec(text);
      if (match) {
        return this.parseNvidiaGPU(match);
      }
    }
    
    // Try AMD patterns
    for (const [key, pattern] of Object.entries(this.gpuPatterns.amd)) {
      const match = pattern.exec(text);
      if (match) {
        return this.parseAMDGPU(match);
      }
    }
    
    // Try Intel patterns
    const arcMatch = this.gpuPatterns.intel.arc.exec(text);
    if (arcMatch) {
      return this.parseIntelGPU(arcMatch);
    }
    
    return undefined;
  }

  /**
   * Parse NVIDIA GPU details
   */
  private parseNvidiaGPU(match: RegExpExecArray): GPUComponent {
    const model = match[0];
    const series = match[1];
    const variant = match[2]; // Ti, Super
    const vramMatch = match[3];
    
    // Determine VRAM based on model
    let vram = 8;
    if (vramMatch) {
      vram = parseInt(vramMatch);
    } else {
      // Default VRAM by model
      if (series === '3060') vram = 12;
      else if (series === '3070') vram = 8;
      else if (series === '3080') vram = 10;
      else if (series === '3090') vram = 24;
      else if (series === '4060') vram = 8;
      else if (series === '4070') vram = 12;
      else if (series === '4080') vram = 16;
      else if (series === '4090') vram = 24;
      else if (series === '1060') vram = 6;
      else if (series === '2060') vram = 6;
    }
    
    // Determine architecture
    let architecture = 'Turing';
    let vramType: GPUComponent['vramType'] = 'GDDR6';
    if (series.startsWith('10')) {
      architecture = 'Pascal';
      vramType = 'GDDR5';
    } else if (series.startsWith('20')) {
      architecture = 'Turing';
    } else if (series.startsWith('30')) {
      architecture = 'Ampere';
      vramType = series === '3090' ? 'GDDR6X' : 'GDDR6';
    } else if (series.startsWith('40')) {
      architecture = 'Ada Lovelace';
      vramType = 'GDDR6X';
    }
    
    // Estimate TDP
    let tdp = 200;
    if (series.startsWith('10')) tdp = 120;
    else if (series === '3060') tdp = 170;
    else if (series === '3070') tdp = 220;
    else if (series === '3080') tdp = 320;
    else if (series === '3090') tdp = 350;
    else if (series === '4070') tdp = 200;
    else if (series === '4080') tdp = 320;
    else if (series === '4090') tdp = 450;
    
    return {
      brand: 'NVIDIA',
      model: model,
      vram,
      vramType,
      tdp,
      outputs: ['HDMI', 'DisplayPort'], // Default
      value: 0,
      condition: 'good',
      miningRisk: false, // Will be updated by risk assessment
    };
  }

  /**
   * Parse AMD GPU details
   */
  private parseAMDGPU(match: RegExpExecArray): GPUComponent {
    const model = match[0];
    const series = match[1];
    const variant = match[2]; // XT
    const vramMatch = match[3];
    
    // Determine VRAM
    let vram = 8;
    if (vramMatch) {
      vram = parseInt(vramMatch);
    } else {
      // Default VRAM by model
      if (series === '580') vram = 8;
      else if (series === '6600') vram = 8;
      else if (series === '6700') vram = 12;
      else if (series === '6800') vram = 16;
      else if (series === '6900') vram = 16;
      else if (series === '7900') vram = variant === 'XT' ? 24 : 20;
    }
    
    // Determine architecture
    let architecture = 'RDNA';
    let vramType: GPUComponent['vramType'] = 'GDDR6';
    if (parseInt(series) < 1000) {
      architecture = 'Polaris';
      vramType = 'GDDR5';
    } else if (series.startsWith('5')) {
      architecture = 'RDNA';
    } else if (series.startsWith('6')) {
      architecture = 'RDNA2';
    } else if (series.startsWith('7')) {
      architecture = 'RDNA3';
    }
    
    // Estimate TDP
    let tdp = 200;
    if (series === '580') tdp = 185;
    else if (series === '6600') tdp = 132;
    else if (series === '6700') tdp = variant === 'XT' ? 230 : 175;
    else if (series === '6800') tdp = variant === 'XT' ? 300 : 250;
    
    return {
      brand: 'AMD',
      model: model,
      vram,
      vramType,
      tdp,
      outputs: ['HDMI', 'DisplayPort'],
      value: 0,
      condition: 'good',
      miningRisk: series === '580', // RX 580 commonly used for mining
    };
  }

  /**
   * Parse Intel GPU details
   */
  private parseIntelGPU(match: RegExpExecArray): GPUComponent {
    const model = match[0];
    const series = match[1];
    
    // Arc GPUs
    let vram = 8;
    let tdp = 225;
    if (series === '750' || series === '770') {
      vram = series === '770' ? 16 : 8;
      tdp = series === '770' ? 225 : 190;
    }
    
    return {
      brand: 'Intel',
      model: model,
      vram,
      vramType: 'GDDR6',
      tdp,
      outputs: ['HDMI', 'DisplayPort'],
      value: 0,
      condition: 'good',
      miningRisk: false,
    };
  }

  /**
   * Detect RAM from text
   */
  detectRAM(text: string): RAMComponent[] | undefined {
    const ramModules: RAMComponent[] = [];
    
    // Try each RAM pattern
    for (const [type, pattern] of Object.entries(this.ramPatterns)) {
      let match;
      while ((match = pattern.exec(text)) !== null) {
        const capacity = parseInt(match[1]);
        const speed = match[2] ? parseInt(match[2]) : 
                     type === 'ddr5' ? 5600 :
                     type === 'ddr4' ? 3200 :
                     type === 'ddr3' ? 1600 : 2400;
        
        // Determine RAM type
        let ramType: RAMComponent['type'] = 'DDR4';
        if (type.includes('ddr5')) ramType = 'DDR5';
        else if (type.includes('ddr3')) ramType = 'DDR3';
        
        // Check if it's a kit (2x8GB, 4x8GB)
        const kitMatch = text.match(/(\d+)\s*x\s*(\d+)\s*gb/i);
        const modules = kitMatch ? parseInt(kitMatch[1]) : 1;
        const perModule = kitMatch ? parseInt(kitMatch[2]) : capacity;
        
        ramModules.push({
          size: capacity,
          speed,
          type: ramType,
          modules,
          value: 0,
          condition: 'good',
        });
        
        // Prevent duplicate detection
        break;
      }
    }
    
    return ramModules.length > 0 ? ramModules : undefined;
  }

  /**
   * Detect storage from text
   */
  detectStorage(text: string): StorageComponent[] | undefined {
    const storage: StorageComponent[] = [];
    
    // Try each storage pattern
    for (const [type, pattern] of Object.entries(this.storagePatterns)) {
      let match;
      while ((match = pattern.exec(text)) !== null) {
        const capacityStr = match[1];
        const isTB = match[0].toLowerCase().includes('tb');
        const capacity = isTB ? parseInt(capacityStr) * 1000 : parseInt(capacityStr);
        
        let storageType: StorageComponent['type'] = 'HDD';
        if (type === 'nvme') storageType = 'NVMe';
        else if (type === 'ssd') storageType = 'SATA SSD';
        
        storage.push({
          type: storageType,
          capacity,
          value: 0,
          condition: 'good',
        });
      }
    }
    
    return storage.length > 0 ? storage : undefined;
  }

  /**
   * Detect motherboard from text
   */
  detectMotherboard(text: string): MotherboardComponent | undefined {
    // Common motherboard patterns
    const patterns = {
      asus: /(?:asus\s*)?(?:rog|tuf|prime)\s*([a-z]\d{3}[a-z\-]*)/gi,
      msi: /(?:msi\s*)?(?:mag|mpg|meg)\s*([a-z]\d{3}[a-z\-]*)/gi,
      gigabyte: /(?:gigabyte\s*)?(?:aorus\s*)?([a-z]\d{3}[a-z\-]*)/gi,
      generic: /([a-z]\d{3})\s*(?:motherboard|mobo|mainboard)/gi,
    };
    
    for (const [brand, pattern] of Object.entries(patterns)) {
      const match = pattern.exec(text);
      if (match) {
        const model = match[0];
        
        // Determine chipset from model
        let chipset = 'Unknown';
        let socket = 'Unknown';
        
        // Intel chipsets
        if (model.includes('Z690') || model.includes('B660')) {
          chipset = match[1] || 'LGA1700';
          socket = 'LGA1700';
        } else if (model.includes('Z590') || model.includes('B560')) {
          chipset = match[1] || 'LGA1200';
          socket = 'LGA1200';
        }
        // AMD chipsets
        else if (model.includes('X570') || model.includes('B550')) {
          chipset = match[1] || 'AM4';
          socket = 'AM4';
        } else if (model.includes('X670') || model.includes('B650')) {
          chipset = match[1] || 'AM5';
          socket = 'AM5';
        }
        
        // Determine form factor
        let formFactor: MotherboardComponent['formFactor'] = 'ATX';
        if (model.toLowerCase().includes('itx')) formFactor = 'ITX';
        else if (model.toLowerCase().includes('matx') || model.includes('-M')) formFactor = 'mATX';
        
        return {
          brand: brand.charAt(0).toUpperCase() + brand.slice(1),
          model,
          chipset,
          socket,
          formFactor,
          ramSlots: formFactor === 'ITX' ? 2 : 4,
          maxRam: socket === 'AM5' || socket === 'LGA1700' ? 128 : 64,
          value: 0,
          condition: 'good',
        };
      }
    }
    
    return undefined;
  }

  /**
   * Detect PSU from text
   */
  detectPSU(text: string): PSUComponent | undefined {
    const wattageMatch = this.psuPatterns.wattage.exec(text);
    if (!wattageMatch) return undefined;
    
    const wattage = parseInt(wattageMatch[1]);
    
    // Detect efficiency rating
    let efficiency: PSUComponent['efficiency'] = '80+';
    const efficiencyMatch = this.psuPatterns.efficiency.exec(text);
    if (efficiencyMatch) {
      efficiency = efficiencyMatch[1].replace(/\s+/g, ' ').trim() as PSUComponent['efficiency'];
    }
    
    // Detect modular type
    let modular: PSUComponent['modular'] = 'non-modular';
    if (text.toLowerCase().includes('full modular') || text.toLowerCase().includes('fully modular')) {
      modular = 'full-modular';
    } else if (text.toLowerCase().includes('semi modular')) {
      modular = 'semi-modular';
    }
    
    // Try to detect brand
    const brands = ['corsair', 'evga', 'seasonic', 'thermaltake', 'cooler master', 'be quiet'];
    let brand: string | undefined;
    for (const b of brands) {
      if (text.toLowerCase().includes(b)) {
        brand = b.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
        break;
      }
    }
    
    return {
      wattage,
      efficiency,
      modular,
      brand,
      value: 0,
      condition: 'good',
    };
  }

  /**
   * Detect case from text
   */
  detectCase(text: string): CaseComponent | undefined {
    // Case detection is more heuristic-based
    const caseKeywords = ['case', 'tower', 'chassis'];
    const hasCase = caseKeywords.some(kw => text.toLowerCase().includes(kw));
    
    if (!hasCase) return undefined;
    
    // Detect form factor
    let formFactor: CaseComponent['formFactor'] = 'Mid Tower';
    if (text.toLowerCase().includes('full tower')) formFactor = 'Full Tower';
    else if (text.toLowerCase().includes('mini tower') || text.toLowerCase().includes('itx')) formFactor = 'Mini Tower';
    else if (text.toLowerCase().includes('sff') || text.toLowerCase().includes('small form')) formFactor = 'SFF';
    
    // Detect side panel
    let sidePanel: CaseComponent['sidePanel'] = 'solid';
    if (text.toLowerCase().includes('tempered glass')) sidePanel = 'tempered glass';
    else if (text.toLowerCase().includes('window')) sidePanel = 'windowed';
    
    // Detect color
    let color = 'black';
    if (text.toLowerCase().includes('white')) color = 'white';
    else if (text.toLowerCase().includes('silver')) color = 'silver';
    
    // Try to detect brand
    const brands = ['nzxt', 'corsair', 'fractal', 'lian li', 'phanteks', 'cooler master'];
    let brand: string | undefined;
    for (const b of brands) {
      if (text.toLowerCase().includes(b)) {
        brand = b.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
        break;
      }
    }
    
    return {
      brand,
      formFactor,
      color,
      sidePanel,
      value: 0,
      condition: 'good',
    };
  }

  /**
   * Detect cooling from text
   */
  detectCooling(text: string): CoolingComponent | undefined {
    const textLower = text.toLowerCase();
    
    // Detect cooling type
    let type: CoolingComponent['type'] = 'stock';
    let size: number | undefined;
    
    if (textLower.includes('custom loop') || textLower.includes('water cooling loop')) {
      type = 'custom-loop';
    } else if (textLower.includes('aio') || textLower.includes('all in one')) {
      type = 'aio';
      // Try to detect radiator size
      const sizeMatch = text.match(/(\d{3})\s*mm/i);
      if (sizeMatch) {
        size = parseInt(sizeMatch[1]);
      }
    } else if (textLower.includes('air cooler') || textLower.includes('tower cooler')) {
      type = 'air';
    }
    
    // Try to detect brand
    const brands = ['corsair', 'nzxt', 'arctic', 'noctua', 'be quiet', 'cooler master', 'deepcool'];
    let brand: string | undefined;
    for (const b of brands) {
      if (textLower.includes(b)) {
        brand = b.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
        break;
      }
    }
    
    return {
      type,
      brand,
      size,
      value: 0,
      condition: 'good',
    };
  }
}