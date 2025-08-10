/**
 * Detection Avoidance
 * Techniques to avoid being detected as a bot
 */

export interface DetectionConfig {
  minDelay: number;
  maxDelay: number;
  userAgent?: string;
  viewport?: {
    width: number;
    height: number;
  };
}

export class DetectionAvoider {
  private config: DetectionConfig;
  
  constructor(config: DetectionConfig = {
    minDelay: 500,
    maxDelay: 2000
  }) {
    this.config = config;
  }
  
  /**
   * Random delay between actions
   */
  async randomDelay(): Promise<void> {
    const delay = Math.random() * (this.config.maxDelay - this.config.minDelay) + this.config.minDelay;
    return new Promise(resolve => setTimeout(resolve, delay));
  }
  
  /**
   * Human-like mouse movement coordinates
   */
  generateMousePath(start: { x: number; y: number }, end: { x: number; y: number }): Array<{ x: number; y: number }> {
    const steps = 20;
    const path: Array<{ x: number; y: number }> = [];
    
    for (let i = 0; i <= steps; i++) {
      const t = i / steps;
      // Add some randomness to make it look natural
      const noise = (Math.random() - 0.5) * 10;
      
      path.push({
        x: start.x + (end.x - start.x) * t + noise,
        y: start.y + (end.y - start.y) * t + noise
      });
    }
    
    return path;
  }
  
  /**
   * Random scroll behavior
   */
  async humanScroll(element: HTMLElement): Promise<void> {
    const scrollSteps = 3 + Math.floor(Math.random() * 5);
    
    for (let i = 0; i < scrollSteps; i++) {
      const scrollAmount = 100 + Math.random() * 200;
      element.scrollTop += scrollAmount;
      await this.randomDelay();
    }
  }
  
  /**
   * Type text with human-like delays
   */
  async typeText(text: string, callback: (char: string) => void): Promise<void> {
    for (const char of text) {
      callback(char);
      // Typing speed varies between 50-150ms
      const typingDelay = 50 + Math.random() * 100;
      await new Promise(resolve => setTimeout(resolve, typingDelay));
    }
  }
}