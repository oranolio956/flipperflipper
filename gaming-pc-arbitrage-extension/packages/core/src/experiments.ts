/**
 * A/B Testing and Experiments
 */

export interface Experiment {
  id: string;
  name: string;
  variants: Array<{
    id: string;
    weight: number;
  }>;
  active: boolean;
}

export class ExperimentManager {
  private experiments: Map<string, Experiment> = new Map();
  
  createExperiment(experiment: Experiment): void {
    this.experiments.set(experiment.id, experiment);
  }
  
  getVariant(experimentId: string, userId: string): string | null {
    const experiment = this.experiments.get(experimentId);
    if (!experiment || !experiment.active) return null;
    
    // Simple hash-based assignment
    const hash = this.hashCode(userId + experimentId);
    const normalized = Math.abs(hash) % 100;
    
    let cumulative = 0;
    for (const variant of experiment.variants) {
      cumulative += variant.weight;
      if (normalized < cumulative) {
        return variant.id;
      }
    }
    
    return experiment.variants[0]?.id || null;
  }
  
  private hashCode(str: string): number {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash;
    }
    return hash;
  }
}